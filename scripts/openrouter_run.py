#!/usr/bin/env python3
"""Ask BuddhistBench items to many models through OpenRouter, in several search modes.

One-off leaderboard run:
  OPENROUTER_API_KEY=... python3 scripts/openrouter_run.py \
      --items tracks/37-practices/data/en/dev.jsonl \
      --models anthropic/claude-sonnet-4.5 openai/gpt-5 \
      --modes closed-book native-search logged-search --variants plain sourced \
      --out tracks/37-practices/results/en/runs

Daily study run (reads items, panel and interventions from study.json):
  python3 scripts/openrouter_run.py --study studies/<id>

Dry run with fake model and search (no network, no key), for CI and format checks:
  python3 scripts/openrouter_run.py --study studies/example-37-practices --dry-run --out /tmp/run

Modes (docs/intervention-study.md):
  closed-book    no tools
  native-search  OpenRouter server tool openrouter:web_search, engine=native; the model decides.
                 We see search counts and cited URLs, not queries or uncited results.
  logged-search  our own web_search / fetch_url function tools; the model decides; everything logged.
                 Needs BRAVE_API_KEY (or --search-backend fake).
  forced-search  OpenRouter's web plugin (always searches once; deprecated by OpenRouter).

Writes one folder per (model, mode, variant): run.json, calls.jsonl (schema/call.schema.json),
responses.jsonl (repeat 0) and scores.json (scripts/score.py report + search stats).
Standard library only.
"""
import argparse
import hashlib
import html
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score  # noqa: E402
import urlmatch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RUNNER_VERSION = "0.1.0"
PROMPT_VERSION = "0.2.0"
API = "https://openrouter.ai/api/v1"
UA = "BuddhistBench/0.2 (+https://github.com/BuddhistAI/buddhist-bench)"
MODES = ["closed-book", "native-search", "logged-search", "forced-search"]
TOOL_MODES = {"native-search", "logged-search"}
OBSERVABILITY = {"closed-book": "none", "native-search": "counts-and-citations",
                 "logged-search": "full", "forced-search": "citations"}
MAX_TOOL_ROUNDS = 6

# ---------------------------------------------------------------- prompts (prompts/answer.md)

SYSTEM = ("You are answering questions about Buddhism. Answer accurately and concisely. If a question names a "
          "tradition, answer from that tradition's point of view. If traditions disagree and the question does not "
          "name one, say which traditions hold which views. If you do not know, or the question rests on something "
          "that does not exist, say so instead of guessing.")
REPLY = {
    ("mcq", "plain"): "Reply with only the letter of your answer, or DECLINE if you cannot answer.",
    ("short", "plain"): "Reply with only the answer, in as few words as possible, or DECLINE if you cannot answer.",
    ("open", "plain"): "Answer in at most 200 words.",
    ("mcq", "sourced"): ("Reply with the letter of your answer on the first line, or DECLINE. "
                         "Then list the reliable sources that support it."),
    ("short", "sourced"): ("Reply with the answer on the first line, in as few words as possible, or DECLINE. "
                           "Then list the reliable sources that support it."),
    ("open", "sourced"): "Answer in at most 200 words, and cite reliable sources for your answer.",
}
TOOLS = [
    {"type": "function", "function": {
        "name": "web_search", "description": "Search the web. Returns up to 8 results with title, URL and snippet.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "fetch_url", "description": "Fetch a web page and return its text (first 8,000 characters).",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
]


def user_prompt(item, variant):
    parts = [item["question"]]
    if item["format"] == "mcq":
        parts.append("\n".join(f"{c['id']}. {c['text']}" for c in item["choices"]))
    parts.append(REPLY[(item["format"], variant)])
    return "\n\n".join(parts)


def extract(item, text):
    """-> (answer, declined) following prompts/answer.md."""
    text = (text or "").strip()
    if not text:
        return None, False
    if item["format"] == "open":
        return text, False
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    first = re.sub(r"^\W*(answer|final answer)\s*[:\-]\s*", "", first.strip().strip("*_ "), flags=re.I).strip("*_ ")
    if first.upper().startswith("DECLINE"):
        return None, True
    if item["format"] == "mcq":
        ids = {c["id"].upper() for c in item["choices"]}
        m = re.match(r"^\(?([A-Za-z])\b", first)
        return (m.group(1).upper() if m and m.group(1).upper() in ids else first), False
    return first.rstrip(". "), False


# ---------------------------------------------------------------- HTTP

def http_json(url, body=None, headers=None, timeout=180, retries=4):
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})},
                                     method="POST" if data else "GET")
        if data:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            if e.code in (408, 429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(2 ** attempt + random.random())
                continue
            raise RuntimeError(f"HTTP {e.code}: {detail}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < retries:
                time.sleep(2 ** attempt + random.random())
                continue
            raise RuntimeError(f"network: {e}") from None


def fetch_text(url, limit=8000):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read(2_000_000).decode(r.headers.get_content_charset() or "utf-8", "replace")
    raw = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", raw)
    return " ".join(html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw)).split())[:limit]


class OpenRouter:
    def __init__(self, key):
        self.h = {"Authorization": f"Bearer {key}", "HTTP-Referer": "https://github.com/BuddhistAI/buddhist-bench",
                  "X-Title": "BuddhistBench"}

    def chat(self, body):
        return http_json(f"{API}/chat/completions", body, self.h)

    def models(self):
        return http_json(f"{API}/models", headers=self.h)["data"]


class Brave:
    name = "brave"

    def __init__(self, key):
        self.key = key

    def search(self, query, n=8):
        q = urllib.parse.urlencode({"q": query, "count": n})
        r = http_json(f"https://api.search.brave.com/res/v1/web/search?{q}",
                      headers={"X-Subscription-Token": self.key, "Accept": "application/json"}, timeout=30)
        return [{"url": x["url"], "title": x.get("title", ""), "snippet": x.get("description", "")}
                for x in r.get("web", {}).get("results", [])[:n]]

    def fetch(self, url):
        return fetch_text(url)


# ---------------------------------------------------------------- fakes for --dry-run

class FakeSearch:
    name = "fake"

    def __init__(self, interventions):
        self.urls = [iv["url"] for iv in interventions]

    def search(self, query, n=8):
        res = [{"url": f"https://example.org/search/{i}?q={urllib.parse.quote(query)}", "title": f"Result {i}",
                "snippet": "Fake result."} for i in range(3)]
        return [{"url": u, "title": "Intervention page", "snippet": "Fake."} for u in self.urls] + res

    def fetch(self, url):
        return "Fake page text."


class FakeOpenRouter:
    """Deterministic fake: answers correctly about half the time, searches in tool modes."""

    def __init__(self, items, interventions):
        self.items = {i["question"]: i for i in items}
        self.iv_urls = [iv["url"] for iv in interventions]

    def models(self):
        return [{"id": "fake/model-a", "architecture": {"output_modalities": ["text"]},
                 "supported_parameters": ["tools"]},
                {"id": "fake/model-b", "architecture": {"output_modalities": ["text"]}, "supported_parameters": []}]

    def chat(self, body):
        q = body["messages"][1]["content"]
        item = next((i for k, i in self.items.items() if q.startswith(k)), None)
        h = int(hashlib.sha256((body["model"] + q + str(len(body["messages"]))).encode()).hexdigest(), 16)
        usage = {"prompt_tokens": 100, "completion_tokens": 20, "cost": 0.0001}
        if body.get("tools") and body["tools"][0].get("type") == "function" and len(body["messages"]) == 2:
            return {"model": body["model"], "provider": "Fake", "usage": usage, "choices": [{"message": {
                "role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {
                    "name": "web_search", "arguments": json.dumps({"query": q[:60]})}}]}}]}
        ans = item["positions"][0]["answer"] if item and h % 2 else "I am not sure"
        msg = {"role": "assistant", "content": ans, "annotations": []}
        if body.get("tools") or body.get("plugins"):
            usage["server_tool_use_details"] = {"web_search_requests": h % 2}
            if self.iv_urls and h % 3 == 0:
                msg["annotations"] = [{"type": "url_citation", "url_citation": {"url": self.iv_urls[0], "title": "x"}}]
        return {"model": body["model"], "provider": "Fake", "usage": usage, "choices": [{"message": msg}]}


# ---------------------------------------------------------------- one call

def content_text(msg):
    c = msg.get("content")
    if isinstance(c, list):
        return "".join(p.get("text", "") for p in c if isinstance(p, dict))
    return c or ""


def ask(client, search, item, model, mode, variant, temperature, engine):
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_prompt(item, variant)}]
    body = {"model": model, "messages": messages, "usage": {"include": True}}
    if temperature is not None:
        body["temperature"] = temperature
    params = {"temperature": temperature}
    if mode == "native-search":
        body["tools"] = [{"type": "openrouter:web_search", "parameters": {"engine": engine}}]
        params["engine"] = engine
    elif mode == "forced-search":
        body["plugins"] = [{"id": "web"}]
    elif mode == "logged-search":
        body["tools"] = TOOLS
        params["search_backend"] = search.name

    s = {"triggered": None, "requests": None, "queries": [], "results": [], "fetched_urls": [], "cited_urls": [],
         "observability": OBSERVABILITY[mode]}
    usage_total, served, provider = {}, None, None
    for _ in range(MAX_TOOL_ROUNDS + 1):
        resp = client.chat(body)
        served, provider = resp.get("model", served), resp.get("provider", provider)
        for k, v in (resp.get("usage") or {}).items():
            if isinstance(v, (int, float)):
                usage_total[k] = usage_total.get(k, 0) + v
            elif isinstance(v, dict):
                d = usage_total.setdefault(k, {})
                for kk, vv in v.items():
                    if isinstance(vv, (int, float)):
                        d[kk] = d.get(kk, 0) + vv
        msg = resp["choices"][0]["message"]
        calls = [c for c in msg.get("tool_calls") or [] if c.get("type", "function") == "function"]
        if mode != "logged-search" or not calls:
            break
        messages.append({"role": "assistant", "content": msg.get("content"), "tool_calls": calls})
        for c in calls:
            fn = c["function"]["name"]
            try:
                arg = json.loads(c["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                arg = {}
            try:
                if fn == "web_search":
                    qi = len(s["queries"])
                    s["queries"].append(arg.get("query", ""))
                    res = search.search(arg.get("query", ""))
                    s["results"] += [{"query_index": qi, "rank": r + 1, "url": x["url"], "title": x["title"]}
                                     for r, x in enumerate(res)]
                    out = json.dumps(res, ensure_ascii=False)
                elif fn == "fetch_url":
                    s["fetched_urls"].append(arg.get("url", ""))
                    out = search.fetch(arg.get("url", ""))
                else:
                    out = f"Unknown tool {fn}"
            except Exception as e:  # tool errors go back to the model, as a real tool would
                out = f"Error: {e}"
            messages.append({"role": "tool", "tool_call_id": c["id"], "content": out})
    else:
        msg = {"content": ""}

    text = content_text(msg)
    ann = [a["url_citation"]["url"] for a in msg.get("annotations") or []
           if a.get("type") == "url_citation" and a.get("url_citation", {}).get("url")]
    s["cited_urls"] = sorted(set(ann + urlmatch.urls_in_text(text)))
    if mode == "closed-book":
        s["triggered"], s["requests"] = False, 0
    elif mode == "logged-search":
        s["triggered"], s["requests"] = bool(s["queries"]), len(s["queries"])
    elif mode == "forced-search":
        s["triggered"], s["requests"] = True, 1
    else:
        n = (usage_total.get("server_tool_use_details") or {}).get("web_search_requests")
        s["requests"] = n
        s["triggered"] = (n > 0) if n is not None else (True if ann else None)
    return text, s, usage_total, served, provider, params


# ---------------------------------------------------------------- main

def load_jsonl(path):
    return [json.loads(ln) for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def git_sha():
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--study", help="studies/<id>: take items, panel and interventions from study.json")
    ap.add_argument("--items", nargs="+", help="item .jsonl files (overrides the study's)")
    ap.add_argument("--models", nargs="+", help="OpenRouter model IDs, or 'all'")
    ap.add_argument("--filter", help="regex on model IDs, with --models all")
    ap.add_argument("--exclude", help="regex on model IDs to skip")
    ap.add_argument("--modes", nargs="+", choices=MODES)
    ap.add_argument("--variants", nargs="+", choices=["plain", "sourced"])
    ap.add_argument("--repeats", type=int)
    ap.add_argument("--temperature", type=float, help="default: provider default (or the study's)")
    ap.add_argument("--engine", default="native", help="engine for native-search (native, auto, exa, ...)")
    ap.add_argument("--search-backend", choices=["brave", "fake"])
    ap.add_argument("--include-examples", action="store_true", help="allow example items (format checks only)")
    ap.add_argument("--out", help="output folder (default: the study's runs/<date>/)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--max-cost", type=float, help="stop starting new calls after this many USD")
    ap.add_argument("--dry-run", action="store_true", help="fake model and search; no network, no key")
    args = ap.parse_args()

    study, interventions = None, []
    if args.study:
        sdir = ROOT / args.study if not Path(args.study).is_absolute() else Path(args.study)
        study = json.loads((sdir / "study.json").read_text(encoding="utf-8"))
        ivp = sdir / "interventions.jsonl"
        interventions = load_jsonl(ivp) if ivp.exists() else []
        interventions = [iv for iv in interventions if iv.get("status") != "planned"]
        panel = study["panel"]
        args.items = args.items or [str(ROOT / "tracks" / study["track"] / "data" / study["language"]
                                        / f"{study['split']}.jsonl")]
        args.models = args.models or panel["models"]
        args.modes = args.modes or panel["modes"]
        args.variants = args.variants or panel["variants"]
        args.repeats = args.repeats or panel["repeats"]
        if args.temperature is None:
            args.temperature = panel.get("temperature")
        args.search_backend = args.search_backend or panel.get("search_backend")
        if args.max_cost is None:
            args.max_cost = study.get("budget_usd_per_day")
        if study.get("example"):
            args.include_examples = True
    if not (args.items and args.models):
        ap.error("give --study, or --items and --models")
    args.modes = args.modes or ["closed-book"]
    args.variants = args.variants or ["plain"]
    args.repeats = args.repeats or 1
    if args.dry_run:
        args.search_backend = "fake"
    args.search_backend = args.search_backend or "brave"

    items = [i for p in args.items for i in load_jsonl(p) if i.get("status") == "active"]
    if study and study.get("items") not in (None, "all"):
        keep = set(study["items"])
        items = [i for i in items if i["id"] in keep]
    if not args.include_examples:
        items = [i for i in items if not i.get("example")]
    if not items:
        sys.exit("no items to run (example items need --include-examples)")
    track = items[0]["track"]
    lang = items[0]["language"]

    if args.dry_run:
        client = FakeOpenRouter(items, interventions)
    else:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            sys.exit("OPENROUTER_API_KEY is not set")
        client = OpenRouter(key)
    search = None
    if "logged-search" in args.modes:
        if args.search_backend == "fake":
            search = FakeSearch(interventions)
        else:
            bk = os.environ.get("BRAVE_API_KEY")
            if not bk:
                print("BRAVE_API_KEY not set: skipping logged-search", file=sys.stderr)
                args.modes = [m for m in args.modes if m != "logged-search"]
            else:
                search = Brave(bk)

    catalog = {}
    if args.models == ["all"] or args.dry_run:
        catalog = {m["id"]: m for m in client.models()}
    if args.models == ["all"]:
        models = [m for m, d in catalog.items() if "text" in (d.get("architecture") or {}).get("output_modalities", ["text"])]
        if args.filter:
            models = [m for m in models if re.search(args.filter, m)]
    else:
        models = list(args.models)
    if args.exclude:
        models = [m for m in models if not re.search(args.exclude, m)]

    now = datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")
    if args.out:
        out = Path(args.out)
    elif study:
        out = sdir / "runs" / date
    else:
        ap.error("give --out")
    out.mkdir(parents=True, exist_ok=True)
    iv_index = urlmatch.intervention_index(interventions)
    track_meta = json.loads((ROOT / "tracks" / track / "track.json").read_text(encoding="utf-8"))
    release = (ROOT / "VERSION").read_text().strip()
    sha = git_sha()

    groups, skipped = [], []
    for m in models:
        for mode in args.modes:
            info = catalog.get(m)
            if mode in TOOL_MODES and info is not None and "tools" not in info.get("supported_parameters", []):
                skipped.append({"model": m, "mode": mode, "reason": "model does not list tool support"})
                continue
            for v in args.variants:
                groups.append((m, mode, v))
    jobs = [(g, it, r) for g in groups for it in items for r in range(args.repeats)]
    print(f"{len(models)} models, {len(groups)} model/mode/variant groups, {len(jobs)} calls, "
          f"{len(skipped)} skipped", file=sys.stderr)

    spent = [0.0]
    lock = threading.Lock()
    records = {g: [] for g in groups}

    def work(job):
        (m, mode, v), it, r = job
        with lock:
            if args.max_cost is not None and spent[0] >= args.max_cost:
                return
        run_id = f"{date}-{slug(m)}-{mode}-{v}"
        rec = {"run_id": run_id, "study": study["id"] if study else None, "item_id": it["id"], "repeat": r,
               "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "model": m, "mode": mode,
               "variant": v, "prompt_version": PROMPT_VERSION}
        t0 = time.time()
        try:
            text, s, usage, served, provider, params = ask(client, search, it, m, mode, v, args.temperature,
                                                           args.engine)
            answer, declined = extract(it, text)
            outcome, sc, matched = score.grade_item(it, {"answer": answer, "declined": declined}, None)
            rec.update(served_model=served, provider=provider, params=params, answer=answer, declined=declined,
                       raw=text, search=s, outcome=outcome, score=round(sc, 4), matched=matched, usage=usage,
                       error=None)
            if iv_index:
                rec["interventions"] = {
                    "seen": urlmatch.match([x["url"] for x in s["results"]], iv_index),
                    "fetched": urlmatch.match(s["fetched_urls"], iv_index),
                    "cited": urlmatch.match(s["cited_urls"], iv_index)}
            with lock:
                spent[0] += float(usage.get("cost", 0) or 0)
        except Exception as e:
            rec.update(answer=None, declined=False, raw=None, outcome="not_attempted", score=0.0, matched=[],
                       search={"triggered": None, "observability": OBSERVABILITY[mode]}, error=str(e)[:500])
        rec["latency_ms"] = int((time.time() - t0) * 1000)
        with lock:
            records[(m, mode, v)].append(rec)

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        list(ex.map(work, jobs))

    for (m, mode, v), recs in records.items():
        if not recs:
            continue
        recs.sort(key=lambda x: (x["item_id"], x["repeat"]))
        run_id = recs[0]["run_id"]
        d = out / run_id
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "calls.jsonl", "w", encoding="utf-8") as f:
            for rec in recs:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        reports = []
        for r in range(args.repeats):
            resps = {x["item_id"]: {"id": x["item_id"], "answer": x.get("answer"), "declined": x.get("declined"),
                                    "search": x.get("search")} for x in recs if x["repeat"] == r}
            reports.append(score.build_report(items, resps))
            if r == 0:
                with open(d / "responses.jsonl", "w", encoding="utf-8") as f:
                    for resp in resps.values():
                        f.write(json.dumps(resp, ensure_ascii=False) + "\n")
        rep = reports[0]
        per_rep = [x["overall"].get("score") for x in reports if x["overall"]]
        rep["repeats"] = {"n": args.repeats, "overall_scores": per_rep,
                          "mean": round(sum(per_rep) / len(per_rep), 4) if per_rep else None}
        rep["errors"] = sum(1 for x in recs if x.get("error"))
        (d / "scores.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        run = {
            "benchmark": "buddhist-bench", "release": release, "track": track,
            "track_version": track_meta.get("version"), "language": lang,
            "split": "example" if all(i.get("example") for i in items) else (study or {}).get("split", "dev"),
            "model": m, "served_models": sorted({x.get("served_model") for x in recs if x.get("served_model")}),
            "providers": sorted({x.get("provider") for x in recs if x.get("provider")}),
            "mode": mode, "variant": v, "prompt_version": PROMPT_VERSION, "repeats": args.repeats,
            "temperature": args.temperature, "engine": args.engine if mode == "native-search" else None,
            "search_backend": search.name if (mode == "logged-search" and search) else None,
            "harness": f"BuddhistAI/buddhist-bench@{sha}:scripts/openrouter_run.py (runner {RUNNER_VERSION})",
            "scorer_version": score.SCORER_VERSION, "judge_panel": None, "study": study["id"] if study else None,
            "date": date, "started_at": now.isoformat(timespec="seconds"),
            "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "calls": len(recs), "cost_usd": round(sum(float((x.get("usage") or {}).get("cost", 0) or 0)
                                                       for x in recs), 4),
            "dry_run": args.dry_run, "by": "WeBuddhist",
        }
        (d / "run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if skipped:
        (out / "skipped.json").write_text(json.dumps(skipped, indent=2) + "\n", encoding="utf-8")
    print(f"done: {sum(len(v) for v in records.values())} calls, ${spent[0]:.4f}, written to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
