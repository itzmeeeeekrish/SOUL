# Public Message Dataset Source Review

**Reviewed:** 10 November 2026  
**Purpose:** Identify candidate sources for a later, traceable SOUL baseline. This is a source review—not approval to download, merge or redistribute any raw messages.

## Candidate 1 — UCI SMS Spam Collection

- **Publisher:** UCI Machine Learning Repository.
- **Published/donated:** UCI page records donation on 21 June 2012; the cited research paper is from 2011.
- **Size and labels:** 5,574 English SMS messages labelled ham/spam.
- **Licence:** CC BY 4.0, as stated on the UCI dataset page.
- **Strength:** Well-known reference baseline with a clearly stated licence and citation.
- **Limitations:** Not India-specific; English-only; ham messages largely originate from the NUS SMS corpus, and spam includes older material from multiple sources. The original two-class labels do not reliably separate non-fraud promotional spam from scams.
- **Decision:** Candidate for a classical English baseline after downloading, inspecting, deduplicating and documenting the exact version. Do not map every old spam item to SOUL's scam class.

Source: https://archive.ics.uci.edu/dataset/228/sms+spam+collection  
Citation: Almeida, T. & Hidalgo, J. (2011). SMS Spam Collection. UCI Machine Learning Repository. DOI: https://doi.org/10.24432/C5CC84.

## Candidate 2 — SMS Phishing Dataset for Machine Learning and Pattern Recognition (Mendeley Data)

- **Creators:** Sandhya Mishra and Devpriya Soni.
- **Published:** 20 June 2022, Version 1.
- **Size and labels:** 5,971 messages: 4,844 ham, 489 spam and 638 smishing.
- **Licence:** CC BY 4.0, as displayed on the Mendeley Data page.
- **Strength:** Separates spam from smishing and documents URL/email/phone indicator fields.
- **Limitations:** The page says some text was extracted from Internet images/screenshots using OCR. It thanks the UCI SMS Spam Collection contributors and links the earlier sources, so duplicates/overlap must be checked before combining it with UCI. Raw text needs a privacy and quality inspection.
- **Decision:** Candidate for review; do not merge with UCI until row-level deduplication, provenance review and a label-consistency audit are complete.

Source: https://data.mendeley.com/datasets/f45bkkt8pr/1  
DOI: https://doi.org/10.17632/f45bkkt8pr.1.

## Candidate 3 — Spam SMS in Hindi Language (IEEE DataPort)

- **Curators listed:** Rajkamal Tutu Ponnekanty Y, Ashutosh Sahoo, Faizal Shanavas Puthiyaveettil, Ramanujam Elangovan and Abirami A M.
- **Published:** 18 December 2024.
- **Size and labels:** 3,894 Hindi SMS messages labelled spam/ham, according to the curator's dataset page.
- **Privacy note:** The curator page says the dataset excludes sensitive personal or financial information.
- **Licence:** The curator summary reviewed here does not show the dataset's licence. Verify the actual IEEE DataPort licence and terms before downloading, using or redistributing it.
- **Limitations:** Spam/ham labels do not necessarily distinguish fraudulent scams from ordinary promotions.
- **Decision:** Strong language-coverage candidate, but not approved for use until the source licence and archive details are checked.

Curator page: https://sites.google.com/cse.nits.ac.in/ramanujamge/publications/datasets-offered  
IEEE DataPort DOI: https://doi.org/10.21227/5y8x-n678.

## Candidate 4 — Hinglish & English Financial Scam/Fraud Text Dataset (Hugging Face)

- **Curator listed:** Anuj Bolewar.
- **Size and language balance:** 3,787 examples; the card describes approximately 3,000 English benign and 700 English scam examples, but only 35 Hinglish scam and 28 Hinglish benign examples.
- **Licence:** CC BY 4.0, as displayed on the dataset page.
- **Provenance:** The page says the English portion derives from UCI SMS Spam Collection plus curated text; the small Hinglish portion is hand-written.
- **Strength:** Directly relevant Indian scam scenarios and a documented Hinglish subset.
- **Limitations:** Very small Hinglish coverage; largely English despite the title; derived data may overlap with UCI. Review row quality, duplicates and attribution before use.
- **Decision:** Candidate for inspection and possible supplemental examples, not a standalone Hinglish benchmark.

Source: https://huggingface.co/datasets/bolewara/hinglish-scam-text-dataset.

## Data-source rules for SOUL

1. Keep a source register with publisher, dataset title/version, URL/DOI, licence, retrieval date and citation.
2. Read the actual dataset terms—not just a search snippet—before use.
3. Preserve required attribution and licence notices when redistributing permitted material.
4. Inspect for personal data, malformed rows, duplicates, language mix and label quality.
5. Do not assume that two datasets are independent because they have different names.
6. Split by source/campaign/template group where possible to reduce leakage.
7. Keep raw third-party files out of Git until the licence, privacy and storage decision is documented. The repository ignores `data/raw/` and `data/private/`.
8. Use the synthetic starter CSV for pipeline development only. It is not evidence of real-world model performance.

## Current decision

No third-party dataset has been imported into the repository yet. Start with synthetic schema-validation examples; next, inspect one candidate archive and its exact licence/provenance before building a combined corpus.
