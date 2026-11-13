# Source

- **Dataset:** [biodatlab/thai_buddhist_studies_exam](https://huggingface.co/datasets/biodatlab/thai_buddhist_studies_exam) on Hugging Face
- **Made by:** Biomedical and Data Lab, Mahidol University (contributors named on the dataset card: Phra Udom Siritientong, Titipat Achakulvisut). The questions come from the Thai national Dhamma exams, 2020, 2022 and 2023, about 4,100 four-option questions in Thai. Source columns: question, a–d, answer (choice text), education_level (candidate group), exam_level (elementary, intermediate, advanced), year.
- **License:** Apache-2.0. Redistributed here under Apache-2.0 terms with this attribution; BuddhistBench's own code and other data stay MIT.
- **Revision:** the Hugging Face commit is recorded in `track.json` (`source.revision`) and in every item's `sources_license` by `scripts/import_nak_tham.py`.
- **Changes made on import:** converted to the BuddhistBench item format; answers matched to choices A–D by text; question number = position in the source file; one paper entry per year, education level and exam level in `papers.json`. Question and choice wording unchanged. Rows the importer could not convert are listed in the import summary, not guessed.
- **Contamination:** the papers have been public online, so models may have seen them. The track is marked `contamination: public`; leave it out with `score.py --exclude-public` to see scores on unpublished material only.
