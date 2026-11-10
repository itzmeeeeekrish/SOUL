# Public Message Dataset Source Review

**Reviewed:** 10 November 2026  
**Purpose:** Identify traceable sources for a later SOUL baseline. This review does not approve blind merging or redistribution of any raw messages.

## Candidate 1 — SMS Phishing Dataset for Machine Learning and Pattern Recognition (Mendeley Data)

- **Creators:** Sandhya Mishra and Devpriya Soni, Jaypee Institute of Information Technology.
- **Published:** 20 June 2022, Version 1.
- **Size and labels:** 5,971 messages: 4,844 legitimate/ham, 489 spam and 638 smishing.
- **Licence:** CC BY 4.0, explicitly shown on the Mendeley dataset record.
- **Format/features:** Raw text and extracted URL, email and phone-presence attributes are described.
- **Collection method:** The record says that messages were obtained from Internet images/screenshots and converted to text using OCR. It also thanks the creators of the UCI SMS Spam Collection for making messages available.
- **Strength:** The three labels map conceptually to SOUL's `legitimate`, `spam` and `scam` classes: ham → legitimate; spam → spam; smishing → scam.
- **Limitations:** OCR can introduce errors; it is not a representative Indian consumer inbox sample; likely overlap with UCI must be quantified; inspect the archive for duplicates and personal information before use.
- **Decision:** **Best initial three-class candidate, pending archive inspection, de-duplication, privacy scan and source attribution.** Do not combine with UCI before cross-dataset de-duplication.

Source: https://data.mendeley.com/datasets/f45bkkt8pr/1  
DOI: https://doi.org/10.17632/f45bkkt8pr.1  
Related paper: https://doi.org/10.1007/s00521-021-06305-y

## Candidate 2 — UCI SMS Spam Collection

- **Creators:** Tiago Almeida and José María Gómez Hidalgo.
- **Published/donated:** UCI records donation on 21 June 2012; associated research paper is from 2011.
- **Size and labels:** 5,574 English messages labelled ham/spam.
- **Licence:** CC BY 4.0, as stated on the UCI dataset record.
- **Source composition:** The UCI record describes a mix of Grumbletext spam, NUS SMS Corpus ham, messages from a PhD thesis and an earlier SMS spam corpus.
- **Strength:** Well-known, clearly cited reference dataset with a stated licence.
- **Limitations:** English-only and old; binary ham/spam labels do not separate promotions from fraud. It should not be mapped directly into SOUL's three classes without careful re-annotation.
- **Decision:** Candidate for a classic English spam benchmark and duplicate checking. Not a stand-alone three-class dataset.

Source: https://archive.ics.uci.edu/dataset/228/sms+spam+collection  
DOI: https://doi.org/10.24432/C5CC84

## Candidate 3 — Indian Telecom SMS Spam Collection (JuniorAlive)

- **Maintainer:** JuniorAlive.
- **Repository:** https://github.com/junioralive/india-spam-sms-classification
- **Licence:** The repository includes an MIT licence and its README says the dataset is shared under MIT.
- **Observed file:** `dataset/spam_ham_india.csv`, fields `Msg` and `Label`.
- **File audit performed:** 2,267 non-empty rows; 1,522 ham and 745 spam. A simple normalised exact-text check found 214 repeated rows. Pattern-only scan flagged 57 rows with Indian-mobile-number-like sequences, 40 with 12-digit sequences, 1 email-like pattern and 179 URLs.
- **Strength:** India-specific message content; useful for checking domain shift and local scenario coverage.
- **Limitations:** Labels are only ham/spam; the spam class may mix promotional messages and fraud. Number-like patterns are not confirmed personal data but must be manually inspected and masked before use. Dataset contribution and consent provenance should be reviewed.
- **Decision:** **Candidate for an India-domain validation/development set after de-duplication, label review and privacy redaction.** Do not treat every spam row as a scam.

The counts above are from a programmatic inspection of the public CSV at the time of review. Pattern matches are flags for manual review, not proof that the rows contain real personal identifiers.

Dataset: https://github.com/junioralive/india-spam-sms-classification  
CSV: https://github.com/junioralive/india-spam-sms-classification/blob/main/dataset/spam_ham_india.csv

## Candidate 4 — Spam SMS in Hindi Language (IEEE DataPort)

- **Curators listed:** Rajkamal Tutu Ponnekanty Y, Ashutosh Sahoo, Faizal Shanavas Puthiyaveettil, Ramanujam Elangovan and Abirami A M.
- **Published:** 18 December 2024.
- **Size and labels:** 3,894 Hindi messages labelled spam/ham, according to the curator page.
- **Privacy note:** The curator page says the dataset excludes sensitive personal or financial information.
- **Licence:** The curator summary reviewed here does not show the actual dataset licence. Check the IEEE DataPort licence/terms before downloading, using or redistributing.
- **Limitations:** Spam is described largely as unsolicited promotions/irrelevant messages. Labels do not distinguish fraudulent scams from advertising.
- **Decision:** Candidate for Hindi language evaluation only after licence verification and label-quality review.

Curator page: https://sites.google.com/cse.nits.ac.in/ramanujamge/publications/datasets-offered  
IEEE DataPort DOI: https://doi.org/10.21227/5y8x-n678

## Candidate 5 — Spam SMS in Dravidian Languages (IEEE DataPort)

- **Curators listed:** Ramanujam Elangovan and Abirami A M.
- **Published:** 2 June 2023, according to the curator page.
- **Size and languages:** Nearly 7,700 SMS examples across English, Tamil, Telugu, Kannada and Malayalam, labelled spam/ham.
- **Privacy note:** The curator page says personal or banking information is not included.
- **Licence:** The curator summary reviewed here does not show the actual dataset licence; verify IEEE DataPort terms first.
- **Limitations:** No Hindi/Hinglish focus and binary spam/ham labels.
- **Decision:** Future multilingual evaluation candidate only; not needed for the first English/Hindi/Hinglish baseline.

Curator page: https://sites.google.com/cse.nits.ac.in/ramanujamge/publications/datasets-offered  
IEEE DataPort DOI: https://doi.org/10.21227/dcym-pd69

## Candidate 6 — Hinglish & English Financial Scam/Fraud Text Dataset (Hugging Face)

- **Curator listed:** Anuj Bolewar.
- **Size:** 3,787 examples, with approximately 3,000 English benign, 700 English scam, and only 63 Hinglish examples (35 scam, 28 benign).
- **Licence:** CC BY 4.0 shown on the dataset card.
- **Provenance:** The English portion is derived partly from UCI SMS Spam Collection; the Hinglish portion is hand-written.
- **Strength:** Indian fraud scenarios such as KYC, UPI, loan, OTP and electricity messages.
- **Limitations:** Very small Hinglish subset, mostly English, overlap with UCI, and two labels rather than the three SOUL classes.
- **Decision:** Candidate for reviewed supplemental examples only; not a representative Hinglish benchmark.

Source: https://huggingface.co/datasets/bolewara/hinglish-scam-text-dataset

## Candidate 7 — LLM-generated balanced spam/smishing dataset (Mendeley, 2025)

- **Creators:** Miriam Munoz and Muhammad Islam.
- **Published:** 4 July 2025, Version 1.
- **Size:** 10,191 ham/spam/smishing examples.
- **Licence:** CC BY 4.0 shown on the Mendeley record.
- **Provenance:** The record says the dataset was created using an LLM and names the 2022 Mishra & Soni dataset as a source.
- **Decision:** Do not treat as independent real-world evidence or an independent test set. It may be considered later as synthetic augmentation after generated examples are identified and checked; keep it separate from real-message evaluation.

Source: https://data.mendeley.com/datasets/vmg875v4xs/1  
DOI: https://doi.org/10.17632/vmg875v4xs.1

## Related public project — ScamShield (India-focused SMS detector)

- **Repository:** https://github.com/jeyadev-jd/ScamShield
- **Release date:** Its `CITATION.cff` records 10 October 2026.
- **Relevance:** It documents an India-focused detector with legitimate/spam/smishing labels, word and character TF-IDF, model comparisons, obfuscation tests and a FastAPI + React interface.
- **Data handling claimed by the project:** It says it de-duplicates UCI and Mishra/Soni sources, uses an Indian Telecom dataset and another ScamShield dataset, and separates promotional spam from smishing with a documented labelling pass.
- **Results:** Reported metrics are the project author's own results and have not been independently reproduced by SOUL.
- **Licence caution:** The public repository page did not expose a root `LICENSE` file in this review. Do not copy its code or redistribute its files unless the applicable licence is verified. Its README and methodology can be studied as a research reference with attribution.

Reference: https://github.com/jeyadev-jd/ScamShield

## Data-source rules for SOUL

1. Keep a source register with publisher, dataset title/version, URL/DOI, licence, retrieval date and citation.
2. Read the actual dataset terms—not just a search snippet—before use.
3. Preserve required attribution and licence notices when redistributing permitted material.
4. Inspect for personal data, malformed rows, duplicates, language mix and label quality.
5. Do not assume that datasets with different names are independent. Check exact and near-duplicate messages across sources before splitting.
6. Split by source/campaign/template group where possible to reduce leakage.
7. Keep raw third-party files out of Git. The repository ignores `data/raw/` and `data/private/`.
8. Do not map generic spam to scam. Promotional spam and fraudulent smishing are different classes.
9. Use synthetic examples for pipeline development only, never as a substitute for an independent real-world test set.

## Current decision

- **Primary three-class candidate:** Mishra & Soni Mendeley 2022, pending archive and privacy inspection.
- **India-domain candidate:** JuniorAlive Indian Telecom SMS collection, pending de-duplication, privacy redaction and manual re-labelling of spam into promotion vs scam where evidence supports it.
- **Hindi candidate:** IEEE Hindi SMS dataset, pending licence and annotation review.
- No third-party dataset has been imported into SOUL yet. Dataset v2 remains synthetic and is only for pipeline/split testing.
