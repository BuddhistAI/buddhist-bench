# Source

- **Dataset:** [biodatlab/thai_buddhist_studies_exam](https://huggingface.co/datasets/biodatlab/thai_buddhist_studies_exam) on Hugging Face
- **Made by:** Biomedical and Data Lab, Mahidol University (contributors named on the dataset card: Phra Udom Siritientong, Titipat Achakulvisut). The questions come from the Thai national Dhamma exams (Nak Tham for monks and novices, Dhamma Studies for lay people), 2020, 2022 and 2023, three levels each, about 4,100 four-option questions in Thai.
- **License:** Apache-2.0. Redistributed here under Apache-2.0 terms with this attribution; BuddhistBench's own code and other data stay MIT.
- **Revision:** the Hugging Face commit is recorded in `track.json` (`source.revision`) and in every item's `sources_license` by `scripts/import_nak_tham.py`.
- **Changes made on import:** converted to the BuddhistBench item format; choice labels (ก ข ค ง) mapped to A–D and stripped from the choice text; one paper entry per year, candidate group and level in `papers.json`. Question and choice wording unchanged. Rows the importer could not convert are listed in the import summary, not guessed.
- **Contamination:** the papers have been public online, so models may have seen them. The track is marked `contamination: public`; leave it out with `score.py --exclude-public` to see scores on unpublished material only.
