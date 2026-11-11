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


## Candidate 1 — local archive audit (11 November 2026)

The downloaded outer ZIP was inspected without executing or extracting its contents. It contains three helper scripts, three PDFs and a nested archive named Dataset_5971.zip. The nested archive contains Dataset_5971.csv (595,987 bytes). The CSV was read directly from the nested archive for metadata-only checks.

### Confirmed CSV structure and counts

- Columns: LABEL, TEXT, URL, EMAIL, PHONE.
- Rows: 5,971, matching the Mendeley record.
- After case-normalising LABEL: ham 4,844; smishing 638; spam 489.
- Blank TEXT rows: 0. Blank LABEL rows: 0.
- Normalised non-empty message texts: 5,831.
- Repeated normalised-text groups: 133 (99 same-label groups and 34 conflicting groups).
- Repeated occurrences beyond the first copy: 140.
- The 34 conflicting groups are smishing + spam conflicts and involve 68 rows. These records must be held out of the first supervised baseline until reviewed; do not arbitrarily pick one label.

### Extracted metadata fields

URL, EMAIL and PHONE each contain only YES/NO values in the inspected CSV. Their YES counts are:

| Source label | URL YES | EMAIL YES | PHONE YES |
|---|---:|---:|---:|
| ham (4,844) | 8 (0.2%) | 1 (<0.1%) | 7 (0.1%) |
| smishing (638) | 100 (15.7%) | 11 (1.7%) | 527 (82.6%) |
| spam (489) | 99 (20.2%) | 7 (1.4%) | 310 (63.4%) |

These are dataset-specific associations, not rules for declaring an individual message fraudulent. Legitimate messages can contain links or phone numbers; scams can contain neither. The metadata fields do not contain the actual URL, email address or phone number.

### Bundled helper-script review

The bundled scripts were read as text only; they were not executed. They appear intended to produce presence flags, but their inclusion in the archive does not prove that these exact scripts generated every CSV metadata value.

- Http_extract.py searches for an http:// or https:// prefix. It can miss bare domains and other URL forms.
- Email_extract.py uses a pattern with lowercase character classes and attempts to support forms such as an address written with " at " or " dot ". It may miss uppercase variants.
- Phone_extract.py contains the source pattern `(\d{3})\D\*(\d{3})\D\*(\d{4})\D\*(\d\*)$`. In this pattern, \D\* means one non-digit followed by a literal asterisk; the final \d\* means a digit followed by a literal asterisk. This is a narrow format, not a general phone-number detector.

Next, independently recompute metadata from TEXT using documented SOUL rules and compare the results with the supplied YES/NO fields. Do not blindly trust the bundled flags as model features.

### Current use decision

The dataset remains a promising three-class development candidate, not yet approved for model training or redistribution. Before approval:

1. Perform a privacy scan on message text locally; do not paste raw message examples into chat or commit the original archive.
2. Review or quarantine the 34 conflicting groups.
3. Deduplicate exact same-label messages before splitting, or at minimum keep duplicate groups together in one split.
4. Check possible overlap with UCI and other candidate sources.
5. Recalculate URL/email/phone indicators from TEXT and compare them with the supplied flags.
6. Confirm attribution and licence obligations for any permitted derivative.

The raw archive remains under data/raw/, which is ignored by Git. No third-party message rows have been committed to the repository.


### Privacy-audit utility added (11 November 2026)

A standard-library script, `data/audit_mendeley_privacy.py`, has been added. It reads the nested CSV directly from the downloaded archive; it does not extract the archive, save message contents, or print matched values. It reports only aggregate row counts for broad email/UPI-like, URL/domain-like, phone/long-number, 12-digit and PAN-like patterns.

**Execution status:** The script is committed, but it has not yet been run against the local archive. Its output is not yet available. Pattern counts are candidate flags only: a long number may be an account/reference/date, an email-shaped string may be a UPI ID, and patterns can produce false positives or miss real identifiers. Manual review must remain local and must not copy raw examples into GitHub or chat.


### First local privacy-scan result (11 November 2026)

The user ran the initial aggregate-only script locally against the downloaded archive. It reported:

| Candidate pattern | Rows flagged |
|---|---:|
| Email/UPI-like | 24 |
| URL/domain-like | 261 |
| Phone/long-number | 709 |
| 12-digit numeric | 40 |
| PAN-like | 0 |
| At least one candidate pattern | 907 |

There were 5,971 source rows and no blank TEXT rows. The 907 rows are approximately 15.2% of the source. Pattern counts overlap and must not be added to derive the union. These are broad regex candidates, not confirmed personal data. Phone/long-number matches may include OTPs, dates, references or account-like values; 12-digit matches are not proof of Aadhaar; zero PAN-like matches does not prove absence of PAN data.

The first scan did not report label-wise distribution or pattern combinations. The script has now been enhanced to report those aggregate breakdowns without printing matched text. **The enhanced version has not yet been run locally.** Do not remove all 907 rows. First examine per-label candidate counts and combinations, then make a documented local review/redaction/quarantine decision.
