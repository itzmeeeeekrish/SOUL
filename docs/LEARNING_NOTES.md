# SOUL – Learning Notes (Simple Hinglish)

Ye file tumhari revision notebook hai. Har naye module ke baad isme concept, code ka flow, testing aur viva questions add karenge.

> **Current status (11 November 2026):** Repository/backend foundation complete; Mendeley 2022 candidate ka local audit, privacy screening, deduplication, redaction and grouped 70/15/15 split complete. First text-only TF-IDF + Logistic Regression baseline trained. Full backend test suite: 39 passed in 5.16s. Validation macro-F1: 0.8682; initial test macro-F1: 0.8915. Dataset source/privacy approval and external validation are still pending.

## 1. SOUL kya banane ki koshish kar raha hai?

SOUL ek digital aur financial safety assistant hai. Iska kaam suspicious activity ko identify karne mein help karna, uska reason samjhana aur user ko safe next step batana hai.

Simple example:

- Kisi user ko suspicious KYC SMS mila.
- SOUL available signal ko analyse karta hai.
- Agar suspicious indicators milte hain, warning deta hai.
- Agar relevant official guidance available hai, uska source dikhata hai.
- User khud decide karta hai ki aage kya action lena hai.

SOUL fraud ko 100% detect karne ki guarantee nahi dega.

## 2. Event aur incident mein difference

- **Event:** Ek individual cheez jo observe hui, jaise SMS, QR code, URL ya bank statement mein transaction row.
- **Incident:** Ek case jisko SOUL investigate kar raha hai.

Ek incident mein sirf ek event bhi ho sakta hai. Example: ek fake KYC SMS bhi ek incident hai.

Agar baad mein ek related QR code aur call information milti hai, toh SOUL evidence ke basis par unhe same incident se connect kar sakta hai.

**Important:** Har event ko connect karna zaroori nahi. Connection tabhi banana hai jab evidence ho.

## 3. Individual detection vs correlation

**Individual detection:** Ek SMS ko alag se check karna. Kya isme urgency, suspicious link ya impersonation indicator hai?

**Correlation:** Do ya zyada events ko compare karna. Kya inmein same URL, phone number ya koi doosra meaningful identifier hai?

Correlation ka matlab ye nahi ki dono events automatically fraud hain. Ye sirf relationship ka evidence deta hai.

## 4. Machine Learning (ML) kya hai?

Machine Learning mein computer examples/data se patterns seekhta hai aur naye example par prediction karta hai.

Example:

- Hum model ko labelled messages dete hain.
- Kuch messages legitimate hote hain aur kuch scam.
- Model text ke patterns seekhta hai.
- Naye message ko classify karne ki koshish karta hai.

Model ka prediction final proof nahi hota. Isliye precision, recall aur false positives check karna important hai.

## 5. NLP kya hai?

NLP ka full form hai **Natural Language Processing**.

Simple words mein: Computer ko human language (English, Hindi, Hinglish) ke text ko process aur analyse karna sikhana.

SOUL mein NLP suspicious message ka text analyse karne ke kaam aa sakta hai.

## 6. Computer Vision kya hai?

Computer Vision computer ko images/video se information nikalne mein help karta hai.

SOUL ke possible uses:

- Screenshot se text nikalna (OCR).
- QR code decode karna.
- Image ke visible indicators analyse karna.

Kisi image ko dekhkar ye declare nahi karna chahiye ki wo fake hai, jab tak reliable evidence na ho.

## 7. RAG kya hai?

RAG ka full form **Retrieval-Augmented Generation** hai.

Simple Hinglish:

Normal LLM apni learned knowledge se answer generate karta hai. RAG mein answer dene se pehle system ek trusted document collection mein relevant information search karta hai. Phir LLM retrieved information ke basis par answer banata hai.

SOUL example:

- SOUL ko suspicious KYC message mila.
- Detection engine ne suspicious indicators identify kiye.
- RAG official bank/cybersecurity guidance retrieve karta hai.
- LLM user ko simple language mein explanation deta hai aur source link show karta hai.

**Yaad rakho:** RAG fraud detector nahi hai. Detection engine risk identify karta hai; RAG relevant guidance retrieve karta hai.

## 8. Database kya hota hai?

Database structured information store karne ki jagah hoti hai.

SOUL mein future tables ho sakti hain:

- Users
- Incidents
- Events
- Evidence
- Extracted entities
- Detector results
- Risk assessments

Har suspicious event ka record rakhna hai toh database useful hai. Personal data ko minimum rakhna aur deletion support karna zaroori hai.

## 9. API kya hoti hai?

API ek defined way hai jisse do software components baat karte hain.

Example:

Android app FastAPI backend ko message-analysis request bhej sakti hai. Backend model se prediction lekar structured response return karta hai.

Simple flow:

Android → API request → Python backend → Model → API response → Android screen

## 10. Git aur GitHub

- **Git:** Code ke changes ka version history maintain karta hai.
- **GitHub:** Git repositories ko online host aur collaborate karne deta hai.
- **Repository:** Project ka organised code/documentation space.
- **Commit:** Changes ka saved checkpoint.
- **Branch:** Main code se alag development line.
- **Pull Request:** Ek branch ke changes ko review karke doosri branch mein merge karne ka proposal.

Commit message example: docs: add project architecture

## 11. Important evaluation metrics

- **Precision:** Model ne jitne items ko scam bola, unmein se kitne actually scam the?
- **Recall:** Dataset mein jitne scam items the, unmein se model ne kitne pakde?
- **F1-score:** Precision aur recall ka balanced measure.
- **False Positive:** Legitimate item ko galti se scam bol dena.
- **False Negative:** Scam item ko galti se legitimate bol dena.

Security project mein dono errors important hain. High recall ke chakkar mein bahut saare legitimate messages ko scam label karna user trust ko damage kar sakta hai.

## 12. Initial viva questions

**Q1. SOUL ka main objective kya hai?**

SOUL ka objective users ko suspicious digital aur financial activity identify karne, samajhne aur safe decisions lene mein help karna hai.

**Q2. Kya SOUL sirf SMS fraud detect karega?**

Nahi. Planned system mein supported messages, URLs, QR codes, images aur authorised financial records analyse karne ka scope hai. Implementation step by step hoga.

**Q3. Incident kya hota hai?**

Incident ek investigation case hai. Isme ek event bhi ho sakta hai aur multiple related events bhi.

**Q4. Cross-channel correlation ki zaroorat kyun hai?**

Kabhi-kabhi multiple interactions mein common indicators hote hain. Correlation unke beech possible relationship identify karne mein help karta hai. Lekin single-event detection ke liye correlation zaroori nahi hai.

**Q5. RAG kyun use kar rahe hain?**

RAG verified documents se relevant guidance retrieve karta hai, jisse AI user ko source-backed explanation de sakta hai.

**Q6. Kya SOUL fraud hone se pehle 100% detect kar sakta hai?**

Nahi. SOUL risk indicators detect karne aur timely warning dene ki koshish karega. Complete protection ki guarantee nahi dega.

**Q7. Kya SOUL bank ke internal system ko monitor karega?**

Nahi. Prototype customer-authorised ya synthetic financial records analyse karega. Bank ke internal Core Banking System ko access karne ka claim nahi hai.

## 13. Session log

Har learning session ke baad update karo:

| Date | Topic | Kya samjha? | Doubts / next revision |
|---|---|---|---|
| 2026-11-09 | Project foundation and GitHub basics | Repository, commit, README and project scope | Practise first Git operations |


## 14. Backend foundation – first practical module

### Backend kya karta hai?

Frontend wo part hai jo user dekhta aur use karta hai. Backend wo part hai jo request receive karta hai, processing karta hai aur response bhejta hai.

SOUL mein Android app future mein backend ko suspicious message bhej sakti hai. Backend us request ko process karke structured result wapas dega.

### FastAPI kya hai?

FastAPI Python ka framework hai jisse hum APIs banate hain. Abhi hum ise sirf ek very small API banane ke liye use kar rahe hain.

### Endpoint kya hota hai?

Endpoint ek URL path hota hai jahan app request bhejti hai.

Abhi humne ek endpoint add kiya hai:
- Method: GET
- Path: /health
- Purpose: Check karna ki backend server chal raha hai ya nahi.

Expected response:

```json
{
  "status": "ok",
  "service": "SOUL API",
  "version": "0.1.0"
}
```

Ye response sirf batata hai ki API process request kar raha hai. Ye abhi database, ML model ya bank integration ko test nahi karta.

### Virtual environment kya hai?

Virtual environment ek project-specific Python space hota hai. Isme SOUL ke packages install honge; dusre Python projects ke packages mix nahi honge.

Windows PowerShell commands:

```powershell
py -3.13 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Command ka meaning:
- `py -3.13 -m venv .venv`: Python 3.13 se .venv naam ka environment banao.
- `Activate.ps1`: us environment ko current terminal mein activate karo.
- `python -m pip install --upgrade pip`: package installer ko update karo.
- `python -m pip install -r requirements.txt`: requirements file mein listed pinned packages install karo.

### Environment variables aur .env

Environment variable ek setting hoti hai jo code se bahar rakhi jaati hai.

Example:
- `SOUL_APP_NAME`: API ka naam.
- `SOUL_APP_VERSION`: API version.
- `SOUL_ENV`: development ya another environment.

.env.example ek safe template hai. Iski copy bana kar local .env file use karte hain. .env GitHub par commit nahi karni, kyunki future mein usme private settings ya secrets aa sakte hain.

### Automated test kya karta hai?

Test automatically check karta hai ki code expected behaviour de raha hai ya nahi. SOUL ke local first run mein 1 test pass hua aur koi warning nahi aayi.

Abhi health test ye check karta hai:
1. /health request ka status code 200 ho.
2. Response mein status ki value ok ho.
3. Service aur version fields present hon.

Test run command, backend folder ke andar:

```powershell
python -m pytest -q
```

**Verification complete (10 November 2026):** API start hua, /health response browser mein check hua aur `python -m pytest -q` ne `1 passed in 0.70s` diya. Isliye Milestone 1 complete mark kiya gaya.

### Backend viva questions

**Q1. Backend kyun use kar rahe hain?**

Backend Android app se requests receive karke processing, model inference aur data management jaise tasks handle karega.

**Q2. FastAPI ka role kya hai?**

FastAPI Python mein API endpoints create karne aur request/response handle karne ka framework hai.

**Q3. Health endpoint kyun banaya?**

Ye sabse basic check hai jisse confirm kar sakte hain ki server start hua hai aur request ka response de raha hai.

**Q4. Virtual environment kyun banaya?**

Taaki SOUL ke Python packages isolated rahein aur dusre projects ke packages se conflict na ho.

**Q5. .env GitHub par kyun nahi daalte?**

Usme private configuration ya future API keys ho sakti hain. Isliye safe placeholders .env.example mein rakhte hain aur actual .env ko ignore karte hain.

## 15. Dataset design – Milestone 2

### Dataset kya hota hai?

Dataset examples ka organised collection hota hai. SOUL ke first detector ke liye har row mein ek message aur uska correct label hoga.

### Humne 3 labels kyun choose kiye?

- **Legitimate:** Normal ya expected message. Example: payment receipt ya appointment reminder.
- **Spam:** Unwanted promotion/junk. Example: restaurant discount advertisement. Har spam message fraud nahi hota.
- **Scam:** Deception ke through money, OTP/PIN, account access ya device control lene ki koshish. Example: fake KYC warning ke saath unverified link.

Agar message ka intent clear nahi hai, toh guess nahi karna. Use review ke liye alag rakhenge.

### Dataset ki important columns

- `message_id`: Har row ka unique ID.
- `text`: Original message.
- `label`: legitimate, spam ya scam.
- `language`: en, hi ya hinglish.
- `scenario`: Message kis context ka hai.
- `campaign_group`: Same campaign/template ke related messages ko group karta hai.
- `origin`: Message synthetic hai ya kisi approved source se aaya hai.
- `annotation_note`: Label dene ka short reason.

### ML model ka input kya hoga?

First baseline mein model ko sirf `text` diya jayega aur `label` predict karna hoga.

`annotation_note`, `scenario` aur `campaign_group` training features nahi banenge. Ye audit aur fair train/test splitting ke liye metadata hain. Same campaign group ko alag train aur test sets mein nahi baantna, warna model similar messages yaad karke misleading score de sakta hai.

### Synthetic dataset kyun?

Humne 24 manually authored synthetic examples banaye:
- 8 legitimate
- 8 spam
- 8 scam

Balanced sample se hum code aur data format test kar sakte hain. Ye real-world messages ka representative sample nahi hai aur is par high accuracy claim nahi kar sakte.

Public dataset candidates ko `data/source_review.md` mein list kiya hai. Licence, duplicates, privacy aur labels inspect hone tak third-party raw data import nahi karenge. CSV validate karne ke liye repository root par `python data/validate_dataset.py` run karo. Ye script required columns, blank values, duplicate IDs, allowed labels/languages aur 8-8-8 starter class count check karti hai.

## 16. Session log

| Date | Topic | Kya samjha? | Doubts / next revision |
|---|---|---|---|
| 2026-11-09 | Project foundation and GitHub basics | Repository, commit, README and project scope | Practise first Git operations |
| 2026-11-10 | Backend foundation verified | FastAPI, /health, config, venv, dependencies and pytest; local result: 1 passed, no warnings | Start Milestone 2 dataset design |
| 2026-11-10 | Dataset design starter | Three labels, schema metadata, campaign grouping and synthetic examples | Validate CSV and review an approved public dataset |


## 17. Train/test split aur data leakage

### Dataset ko split kyun karte hain?

Model ko examples se sikhane ke liye training data chahiye. Lekin model ko naye, unseen examples par test karna bhi zaroori hai.

- **Training set:** Is data se model patterns seekhta hai.
- **Validation set:** Model/settings choose karne ke liye use hota hai.
- **Test set:** Final evaluation ke liye alag rakha jata hai. Isse baar-baar tuning nahi karni chahiye.

### Data leakage kya hota hai?

Maan lo ek fake KYC campaign ke 5 message variants hain. Agar same campaign ke kuch variants training mein aur kuch test mein chale gaye, toh test result misleading ho sakta hai. Model ne naya scam samajhne ke bajaye usi template ke familiar words yaad kar liye ho sakte hain.

Isliye SOUL ke dataset mein `campaign_group` field hai. Same campaign/template family ke messages ko ek hi split mein rakhna hai.

### Current 24-row dataset ki limitation

Starter dataset mein 24 examples hain aur 24 alag campaign_group values hain. Isse file structure aur validator test hota hai, lekin repeated campaign variants ka leakage properly test nahi hota.

Isliye abhi in 24 rows par model accuracy report nahi karni chahiye. Pehle representative aur reviewed data collect/prepare karna hai, campaign groups ko sahi tarah identify karna hai, phir split strategy select karni hai.

### Important rule

Test data ko model training ya hyperparameter tuning ke dauraan use nahi karna. Evaluation tabhi useful hai jab test examples genuinely unseen hon.



## 18. Dataset v2 – campaign groups and fixed splits

Humne v2 mein 84 synthetic SMS examples banaye:
- 28 legitimate
- 28 spam
- 28 scam

Har campaign group mein 4 similar wording variants hain. Total 21 groups hain: 7 groups per label.

### Split breakdown

- Training: 15 groups, 60 messages (20 per label).
- Validation: 3 groups, 12 messages (4 per label).
- Testing: 3 groups, 12 messages (4 per label).

Same campaign ke 4 messages ek hi split mein rahenge. Isse ek template ka variant train aur test dono mein aa kar evaluation ko artificially easy nahi bana sakta.

**Important limitation:** Sirf 1 campaign group per label validation aur test mein hai. Ye splitting logic ka educational demo hai; real-world accuracy estimate nahi. Humein multiple independent, reviewed real-world campaigns chahiye honge.

V2 CSV validate karne ke liye repository root par:

```powershell
python data/validate_dataset.py
```

Expected output:
- 84 rows.
- 28 per class.
- Train 60, validation 12, test 12.
- Campaign leakage check passed.



## 19. Dataset v2 local validation and real-data review

10 November 2026 ko local PowerShell se v2 validator successfully run hua:
- 84 rows, 28 per label.
- Train: 60 rows / 15 groups.
- Validation: 12 rows / 3 groups.
- Test: 12 rows / 3 groups.
- Campaign leakage check passed.
- `git status --short` blank tha, yani local working tree clean tha.

Ab real data ke liye humein label meaning samajhna hoga:

- Mendeley 2022 dataset: ham, spam, smishing. Ye hamari 3-class problem ke sabse close hai. Ham → legitimate, spam → spam, smishing → scam mapping candidate hai, lekin raw archive inspect karne ke baad hi use karna hai.
- Indian Telecom dataset: ham/spam only. Iske spam mein promotion aur fraud dono ho sakte hain. Har spam item ko scam label nahi karna.
- Hindi dataset: ham/spam only; licence aur label details confirm karni hain.

**Rule:** Raw messages ko GitHub par commit nahi karna. Pehle duplicates, personal-data patterns aur label quality inspect karni hai. Sirf approved and redacted derived data use karenge.

Related project ScamShield (released 10 October 2026) bhi Indian scam SMS dataset, de-duplication aur model evaluation discuss karta hai. Uske results author-reported hain; SOUL ne independently reproduce nahi kiye.


## 20. Mendeley 2022 SMS dataset — first local audit (11 November 2026)

### Archive structure

The downloaded archive was inspected without executing its scripts or extracting the CSV. The outer ZIP contains a nested Dataset_5971.zip, and that inner ZIP contains Dataset_5971.csv. We read the CSV directly from the archive using Python's standard-library zipfile and csv modules.

The CSV has five columns:
- LABEL: source category.
- TEXT: SMS message.
- URL: URL-presence flag.
- EMAIL: email-presence flag.
- PHONE: phone-presence flag.

The CSV contains 5,971 rows, matching the published dataset count. After normalising label case:
- ham: 4,844
- smishing: 638
- spam: 489

There are no blank TEXT or LABEL values in this first audit.

### Why we normalise labels

The raw file uses both "Smishing" and "smishing", and both "Spam" and "spam". These are casing variants, not extra classes. Convert labels to lowercase before counting or training.

### Duplicate and label-conflict findings

After normalising message text (lowercase and collapse repeated whitespace):
- 5,831 unique non-empty message texts.
- 133 repeated-text groups.
- 99 repeated groups have one consistent label.
- 34 groups have conflicting labels: smishing + spam.
- Those 34 groups contain 68 rows.

A conflicting group means the same normalised text has been assigned different classes. We must not let those records enter the first baseline as though their labels were certain. Keep them in a review/quarantine file. Same-label duplicate messages should be deduplicated or assigned to the same data split so copies cannot leak between train and test.

### What URL / EMAIL / PHONE mean

In this CSV, all three fields contain YES/NO values, not actual URLs, email addresses or phone numbers. YES counts by class:

| Label | URL YES | EMAIL YES | PHONE YES |
|---|---:|---:|---:|
| ham | 8 / 4,844 | 1 / 4,844 | 7 / 4,844 |
| smishing | 100 / 638 | 11 / 638 | 527 / 638 |
| spam | 99 / 489 | 7 / 489 | 310 / 489 |

These associations describe this dataset only. Presence of a phone number or URL is not proof of fraud, and absence is not proof of safety.

### Why we inspected the original helper scripts

The ZIP includes Phone_extract.py, Http_extract.py and Email_extract.py. We read them as text only; we did not execute them.

- The URL pattern looks for http:// or https:// prefixes, so it may miss bare domains.
- The email pattern uses lowercase character classes and attempts to recognise " at " / " dot " obfuscations.
- The phone pattern is unusually narrow and includes literal asterisks in its expected format.

The helper scripts being bundled with the CSV is not proof they generated the exact CSV flags. We will independently derive features from TEXT and compare them with the supplied YES/NO values.

### Important project decision

For the first baseline:
1. Keep TEXT as the primary input.
2. Map ham → legitimate, smishing → scam and spam → spam only as a provisional source-label mapping, preserving the difference between promotional spam and fraud.
3. Quarantine the 34 conflicting text groups.
4. Deduplicate exact same-label texts or keep duplicates together during splitting.
5. Recompute any URL/email/phone features with SOUL's own documented rules.
6. Run a local privacy scan before using or sharing message text.

Never commit raw third-party SMS messages to GitHub. The raw archive is stored in data/raw/, which is ignored by Git. Do not paste real message contents, phone numbers or email addresses into public issues or chat.

### Viva questions

**Q1. Why not directly trust the URL, EMAIL and PHONE columns?**

They are binary indicators produced by some extraction process. We need to understand that process and compare the flags with independently detected features before using them.

**Q2. Why remove or quarantine conflicting labels?**

The same message has contradictory ground-truth labels. Training on both without review teaches the model inconsistent answers.

**Q3. Does a URL or phone number mean the SMS is a scam?**

No. Legitimate messages can contain URLs and phone numbers. These are contextual features, not proof.

**Q4. Why not train immediately on all 5,971 rows?**

We need to handle contradictory labels, duplicates, privacy and split leakage first. A large dataset can still produce misleading results if its quality is not checked.

| Date | Topic | What was learned | Next step |
|---|---|---|---|
| 2026-11-11 | Mendeley archive and metadata audit | ZIP structure, class counts, binary metadata flags, duplicates, conflicting labels and helper-script limitations | Privacy scan and independently recompute metadata from TEXT |


## 21. Privacy pattern audit script

We added `data/audit_mendeley_privacy.py`. It uses only Python's standard library to read the CSV inside the nested ZIP directly. It does not extract files or write message text to another file.

Run it from the repository root:

```powershell
python data\audit_mendeley_privacy.py
```

It reports the number of rows with broad candidate patterns:
- Email/UPI-like text.
- URL/domain-like text.
- Phone or long-number candidates.
- 12-digit numeric candidates.
- PAN-like candidates.
- Rows with at least one of those candidates.

**Important:** A regex only finds a shape that resembles something. A 10-digit sequence could be a phone number, account/reference number or another value. A 12-digit sequence is not proof of Aadhaar. An email-shaped string can also be a UPI ID. These counts are for risk triage, not proof of exposed personal information.

The script deliberately prints no SMS content or matched value, and it does not claim to prove that the dataset is safe. The audit must still be followed by careful local review, redaction decisions and source/licence checks. Do not paste raw messages or identifiers into chat or commit them to GitHub.

**Current execution status:** Script added to GitHub; awaiting local execution against the downloaded archive. No privacy-scan result has been recorded yet.

### Viva questions

**Q1. What is a regular expression (regex)?**

Regex ek text pattern hota hai. Isse hum search kar sakte hain ki kisi message mein email-jaisi string, URL-jaisa domain ya number sequence hai ya nahi.

**Q2. Does a regex match prove that personal data is present?**

No. Regex only flags a possible pattern. The match may be a false positive, and a real identifier may also be missed.

**Q3. Why does the privacy script print counts instead of messages?**

Taaki dataset audit karte waqt raw SMS ya possible personal identifiers terminal logs, screenshots or shared chat mein expose na hon.


## 22. First privacy scan — aggregate findings

The initial local run of `python data\audit_mendeley_privacy.py` completed successfully and reported:

- 5,971 source rows; 0 blank TEXT rows.
- 24 email/UPI-like candidates.
- 261 URL/domain-like candidates.
- 709 phone/long-number candidates.
- 40 12-digit numeric candidates.
- 0 PAN-like candidates.
- 907 rows with at least one candidate pattern (about 15.2%).

**How to interpret this:** These counts overlap. One row may contain multiple kinds of patterns. A long digit sequence may be an OTP, date, transaction reference or account-like number rather than a phone number. A 12-digit match does not establish that it is Aadhaar. No PAN-like pattern was found, but regex limitations mean this does not prove no PAN information exists.

The enhanced version was subsequently run locally and produced the label-wise breakdown:

| Label | Rows | At least one candidate | Email/UPI | URL/domain | Phone/long number | 12-digit | PAN |
|---|---:|---:|---:|---:|---:|---:|---:|
| ham | 4,844 | 20 | 1 | 16 | 6 | 0 | 0 |
| smishing | 638 | 605 | 13 | 126 | 506 | 29 | 0 |
| spam | 489 | 282 | 10 | 119 | 197 | 11 | 0 |

Thus, 0.4% of ham, 94.8% of smishing and 57.7% of spam messages had at least one candidate pattern. This is a pattern in this dataset, not a general fraud rule. Combination counts also showed that 5,064 rows had no match, 614 matched only phone/long-number, 55 matched URL/domain plus phone/long-number, and 23 matched phone/long-number plus 12-digit.

**Decision:** Do not delete all 907 flagged rows automatically. First review the label-wise distribution and pattern combinations. Then locally review any candidate examples only in a private environment, mask them where needed, and keep raw third-party data out of GitHub and chat.


## 23. Local masked privacy review

We added `data/create_masked_privacy_review.py`. It reads the nested archive locally and writes only the candidate rows to:

`data/private/mendeley_privacy_review_masked.csv`

Run it from the repository root:

```powershell
python data\create_masked_privacy_review.py
```

It includes the source row number, source label, detected pattern categories and a masked message body. The script replaces candidate URLs/domains, email/UPI-like strings, PAN-like strings, 12-digit sequences and long-number sequences with placeholders.

**Very important:** Masking is not the same as anonymisation. A name, address, bank detail or personal context may remain if the regex does not recognise it. The file is under `data/private/`, which is ignored by Git. Keep it on your local computer only. Do not upload it, commit it or paste its contents into chat. Review the masked text locally; if necessary compare with the original locally, without sharing the raw message.

When you finish, share only aggregate review totals, such as how many candidates were actual contact details, URLs, OTPs, transaction references, dates or false positives. Do not send message text or actual identifiers.

**Current execution status:** The aggregate audit has been run twice (the enhanced result is documented). The masked-review generator is committed but has not yet been run locally.


## 24. Masked candidate review file generated

The user ran:

```powershell
python data\create_masked_privacy_review.py
```

The script wrote 907 candidate rows to:

`data\private\mendeley_privacy_review_masked.csv`

The source-label counts were ham 20, smishing 605 and spam 282. These match the enhanced privacy audit's "ANY" counts. This validates that the generator selected the expected rows; it does not prove that all rows contain personal data or that masking removed every identifier.

### Manual review categories

The latest generator creates an empty `manual_review_category` column automatically. First pull the latest code and rerun `python data\\create_masked_privacy_review.py`; this overwrites the earlier unreviewed file with the new column. Open the CSV only on the local computer and choose one category for each row:

- `phone_or_contact`
- `email_or_upi`
- `website_link`
- `otp`
- `transaction_reference`
- `date_or_amount`
- `other_personal_data`
- `multiple_categories`
- `false_positive`
- `unclear`

Use `multiple_categories` when more than one category genuinely applies and you do not want to choose a primary one. Use `unclear` instead of guessing. A phone number in a scam message can be a scammer's contact number rather than the recipient's personal number; record what the content appears to contain, not who owns it unless the message makes that clear.

Do not paste message bodies or identifiers into chat or GitHub. A masked body may still contain names, locations or financial context not caught by regex. Do not upload the CSV. The parent folder `data/private/` is Git-ignored.

### Count-only review summary

We added `data/summarize_privacy_review.py`. After saving the spreadsheet as CSV UTF-8 with the `manual_review_category` column, run:

```powershell
python data\summarize_privacy_review.py
```

It prints aggregate totals by category and source label only. It does not print message text, matched values or source row numbers. It checks for blank or unrecognised category entries so the review does not silently appear complete.

**Current status:** Masked review CSV created locally; no manual row classification has been completed yet. Count-only summary helper committed but not yet run.


## 25. Reduce manual privacy review using masked templates

We should not ask a person to classify all 907 flagged source rows one by one. Repeated message formats can be reviewed as a group.

Added `data/build_privacy_review_queue.py`. It reads the original ZIP locally, detects candidates, masks them, and groups rows by the normalised masked text. It creates:

`data/private/mendeley_privacy_review_unique_templates.csv`

Each row in this new file represents one masked template, with:
- A generated group ID.
- Number of source messages represented by the template.
- Source labels and counts for those labels.
- A flag when the same masked template occurs with different source labels.
- Detected pattern categories.
- One representative masked message.
- An empty manual review category.

This grouping may combine source messages whose actual identifiers differ but whose masked template is the same. That is useful for reviewing privacy patterns, but it is not a claim that the raw messages are exact duplicates. Do not use these masked template groups for ML train/test splitting or delete any original records based on this grouping.

Run from the repository root:

```powershell
python data\build_privacy_review_queue.py
```

The script prints the number of candidate rows, number of masked templates, number of repeated occurrences grouped and number of groups with conflicting source labels. Review one template at a time, especially conflict groups and ambiguous numeric contexts. You do not need to review every occurrence. The output is local under `data/private/`, is Git-ignored and may still contain personal context missed by regex. Never upload or share it.

Five tests are now in `backend/tests/test_privacy_review_queue.py`. They cover same-label repeated templates, different messages collapsing to the same masked template, identical normalised original text with conflicting labels, different templates and messages with no candidate. The earlier backend suite run passed (`5 passed in 1.43s`), but this latest test refinement has not yet been run locally.

**Next command after pulling:** From the repository root run `git pull origin main`; then `python data\build_privacy_review_queue.py`. Share only the aggregate counts printed by the script.


### Local grouped-review result (11 November 2026)

The queue script ran successfully and reported:
- 5,971 source rows read.
- 907 rows with candidate patterns.
- 705 unique masked templates.
- 202 repeated source occurrences consolidated.
- 35 templates occurring under multiple labels.
- Candidate source rows: ham 20, smishing 605, spam 282.

This reduces the initial list from 907 source rows to 705 masked templates for a potential review. It does not mean 705 distinct real-world scam campaigns or exact duplicate groups. A masked template is created after replacing detected identifiers; two messages with different original phone numbers or URLs can therefore become the same template.

**Do not confuse the 35 multi-label masked templates with the 34 exact normalised-text label conflicts found earlier.** The first count is produced after masking and can include template collisions; the second count is based on normalised original text. They require separate interpretation.

The backend test suite was run locally:
`python -m pytest -q` → `5 passed in 1.43s`.

**Next:** Open `data/private/mendeley_privacy_review_unique_templates.csv` locally and filter `has_exact_text_label_conflict` to `yes` in the latest regenerated queue. Review these 35 templates first. For each, decide privately whether it is (a) the same original text with inconsistent labels, (b) different messages merged by masking, or (c) unclear. Do not paste masked messages into chat. There is no need to manually inspect all 705 templates yet.


### Distinguish real label conflicts from masked-template collisions

A masked template can combine different original messages because their URLs or numbers become the same placeholder. So `source_label_conflict=yes` alone does not prove that the exact same original message received different labels.

The updated `data/build_privacy_review_queue.py` now compares the normalised original message text internally (case-folding and collapsing whitespace) and exports only two safe fields:
- `distinct_source_texts`: how many different normalised original messages collapsed into this masked template.
- `has_exact_text_label_conflict`: yes only when the same normalised original text occurs with more than one label.

No original message text or matched number/link is written to the queue. Use `has_exact_text_label_conflict=yes` to prioritise genuine exact-text label conflicts. Other multi-label templates are masking collisions and may not need label correction.

The tests were expanded to check this distinction. The user reran the latest queue locally and got 34 masked templates containing at least one exact-text label conflict. The same run reported 35 templates with multiple labels, so the difference is a masking collision. The user also reran the backend tests: `6 passed in 1.14s`.


### Latest exact-conflict verification (11 November 2026)

The latest local queue run reported:
- 5,971 source rows.
- 907 rows with candidate patterns.
- 705 unique masked templates.
- 202 repeated occurrences grouped.
- 35 masked templates with multiple source labels.
- 34 masked templates containing an exact-text label conflict.

This matches the earlier raw-text audit of 34 conflicting exact-text groups involving 68 rows. The 35 count is broader because masked templates can merge different original messages.

The updated backend test suite passed locally:
`python -m pytest -q` → `6 passed in 1.14s`.

**Decision for the first baseline:** Keep the 34 exact-text conflict groups (68 rows) in a separate quarantine set until reliable evidence supports a label correction. Do not choose spam or smishing arbitrarily. This does not require reviewing all 705 privacy templates by hand. We can proceed to a reproducible clean-data preparation stage after preserving the quarantine and designing conservative identifier redaction.


## 26. Prepare a clean local derivative before model training

We added `data/prepare_mendeley_dataset.py`. The goal is to automate repetitive data cleanup instead of manually reviewing every flagged source row.

Run it from the repository root:

```powershell
python data\prepare_mendeley_dataset.py
```

It reads the original nested ZIP and creates two files under `data/private/`:

1. `mendeley_prepared.csv`: maps the source labels to SOUL classes, groups messages by case-insensitive text with collapsed whitespace, collapses same-label exact duplicates and masks regex-detected candidate identifiers. It also retains the regex presence indicators and the original YES/NO metadata flags so we can compare them later. For duplicate rows, it checks source-flag consistency across every occurrence; if duplicates disagree, that metadata value is left blank rather than arbitrarily selecting the first row.
2. `mendeley_quarantine.csv`: keeps groups whose exact normalised text has conflicting labels, plus rows with blank text or unexpected labels. The quarantine output contains masked text and aggregate label information, not raw matched values.

### Why quarantine conflicting labels?

A model cannot learn one reliable answer when exactly the same message has two different labels. We should not guess which label is correct. Keep those messages aside unless we can resolve them from reliable annotation evidence.

### Why keep feature flags?

We want to compare a text-only model with a text-plus-metadata model later. The source CSV says whether URL/email/phone indicators were present; the new script independently recomputes candidate flags from the original text. It also counts where those flags disagree. These are candidate features, not proof of fraud.

### Important limitations

- The redaction patterns are broad. A long number may be an OTP, transaction reference, date or phone number. The script replaces candidates with placeholders, which can remove useful context. This is a conservative privacy-first starting point, not a perfect named-entity recogniser.
- Regex can miss a real identifier or leave a person's name, address or other context behind. These outputs are not guaranteed anonymous.
- Same-label exact duplicates are collapsed; near-duplicate campaign variants are not automatically grouped.
- The script does not split data or train a model.
- Keep both outputs in `data/private/`; do not upload, commit or paste them into chat.

Seven unit tests were added in `backend/tests/test_prepare_mendeley_dataset.py`. They cover conflicting-label quarantine, duplicate collapse, source-label mapping, candidate redaction, source-flag mismatch counts, unknown labels and blank text.

**Execution status:** The preparation script and its seven tests are committed but have not yet been run locally.


The preparation script was refined to count source-flag mismatches across all records in a duplicate group and report duplicate groups whose source metadata disagrees. The latest version has not yet been run locally.


## 27. Local preparation result — first clean derivative

The user ran `python data\prepare_mendeley_dataset.py` successfully. It produced:

- Source rows: 5,971.
- Exact normalised-text groups: 5,831.
- Conflicting label groups quarantined: 34 groups / 68 rows.
- Same-label duplicate groups: 99.
- Duplicate rows collapsed: 106.
- Prepared unique records: 5,797.
- Quarantine groups: 34 / 68 source rows.

### Class balance

| Class | Prepared records | Share |
|---|---:|---:|
| legitimate | 4,834 | 83.4% |
| scam | 528 | 9.1% |
| spam | 435 | 7.5% |

This is an imbalanced dataset. A model that always predicts legitimate could appear to achieve about 83.4% accuracy while missing every scam and spam message. So later we must report per-class precision/recall/F1, macro-F1, confusion matrix and false-positive rate, not accuracy alone.

### Metadata mismatch findings

Comparing the source YES/NO flags with SOUL's regex flags gave:
- URL mismatches: 58.
- EMAIL mismatches: 9.
- PHONE mismatches: 180.

Among duplicate groups, source flags were inconsistent within 5 URL groups, 2 EMAIL groups and 6 PHONE groups. The preparation utility leaves the inconsistent source flag blank rather than choosing one arbitrarily.

A mismatch does not automatically mean the source flag is wrong. The dataset creators' original regex and SOUL's independent regex use different detection rules. SOUL's broad number pattern can flag OTPs, dates or transaction references as well as phone numbers. Therefore the first baseline must use redacted TEXT only; keep metadata out of model training until separately validated.

The full backend suite passed locally:
`python -m pytest -q` → `13 passed in 1.22s`.

**Important:** The prepared CSV and quarantine CSV remain in `data/private/`. They are local research files, not reviewed as fully anonymous and not to be committed or uploaded. No train/validation/test split or model training has happened yet.


## 28. Validate prepared data before creating train/test splits

The local preparation run produced 5,797 unique records after quarantining 68 rows with contradictory labels and collapsing 106 repeated rows. Class counts:

- legitimate: 4,834 (83.4%)
- scam: 528 (9.1%)
- spam: 435 (7.5%)

This is class imbalance. A model that predicts "legitimate" for every message could get 83.4% accuracy while catching zero scams and zero spam. Later we must report per-class precision, recall and F1, macro-F1 and a confusion matrix. We should not celebrate accuracy alone.

The original metadata flags differ from SOUL's broad pattern flags on 58 URL, 9 EMAIL and 180 PHONE records. Some exact-duplicate groups also have inconsistent source flags (5 URL, 2 EMAIL, 6 PHONE groups). These mismatches can come from different regex definitions; the phone candidate can also be an OTP, reference or date. **For the first baseline, use redacted TEXT only.** Metadata features will be deferred.

### New prepared-data validator

Added `data/validate_prepared_dataset.py` and five tests in `backend/tests/test_validate_prepared_dataset.py`.

Run from the repository root:

```powershell
python data\validate_prepared_dataset.py
```

It reads the local prepared CSV and prints only aggregate information:
- Empty or duplicate IDs.
- Blank text and invalid labels.
- Invalid binary feature values.
- Residual candidate patterns still detected by the current regex.
- Duplicate masked text groups, including collisions between different labels.
- Class counts and source occurrences represented.

A residual regex count of zero is only a check against our known patterns. It does not prove the messages are anonymous; personal names, addresses and context may remain. The validator does not change files, split data or train a model.

The five validator tests cover a valid record, residual URL detection, same-label masked duplicates, cross-label masked collisions and invalid fields/IDs. These tests are committed but have not yet been run locally.

**Next:** Pull, run the prepared-data validator, then run the complete pytest suite. Only after reviewing masked-text collisions should we create a leakage-aware split. The first model should use text-only features.


## 29. Prepared-data validation result

The local prepared-data validator reported:
- 5,797 records and 5,797 unique record IDs.
- No missing IDs, duplicate IDs, blank text, invalid labels, invalid binary metadata values or invalid source-occurrence values.
- Source occurrences represented: 5,903. This equals 5,971 original rows minus the 68 rows quarantined for contradictory exact-text labels.
- Zero residual matches for the same regex patterns used by our redaction code.
- 5,722 unique normalised masked texts.
- 37 repeated masked-text groups containing 112 records.
- 1 repeated masked-text group with different labels.

**Important:** Zero residual regex matches only says that the known patterns used by our own redaction rules were removed. It is not proof that all personal information has been removed. Names, addresses and other unrecognised context may remain.

### Why we need one more grouping step before train/test split

The prepared CSV has 5,797 rows, but 5,722 unique masked texts. The same final text must not be split across train and test. If identical model input appears in both, evaluation may be too optimistic. If one identical masked text has different labels, the model receives conflicting targets for the exact same input.

So the split builder will:
1. Group records by normalised final masked text.
2. Quarantine a group if its same masked text has more than one label.
3. Collapse same-label repeated masked texts to one model row (sum the source occurrence count for audit).
4. Stratify the remaining unique texts by class into train/validation/test.
5. Use a fixed random seed so the same input produces the same split.

The split will prevent exact masked-text leakage. It will not discover every near-duplicate campaign or prove generalisation to new fraud campaigns.

The user ran the full backend test suite after adding the prepared-data validator:
`python -m pytest -q` → `18 passed in 0.92s`.


## 30. Create a group-safe train/validation/test split

The prepared CSV contains 5,797 records but only 5,722 unique normalised masked texts. Some different original messages become identical after our masking rules. If the exact same final text is present in both train and test, evaluation may be misleading.

We added `data/create_mendeley_splits.py`. It uses only the Python standard library; no new package installation is required.

Run from the repository root:

```powershell
python data\create_mendeley_splits.py
```

### What it does

1. Groups rows by the final redacted text after case-folding and collapsing extra whitespace.
2. If a group has one label, it collapses the repeated model input into one row and sums source occurrence counts for audit.
3. If the same final text has different labels, it quarantines that entire group rather than guessing which label is right.
4. Separately shuffles the three classes using fixed seed 42.
5. Assigns approximately 70% to train, 15% to validation and 15% to test inside each class.
6. Checks that identical final text and group IDs do not cross partitions.

Expected local output directory:

`data/private/mendeley_splits/`

Files:
- `train.csv`
- `validation.csv`
- `test.csv`
- `split_quarantine.csv`

Only `text` should be model input (X), and `label` should be target (y). Other columns are traceability metadata and must not be used as model features.

### Limitations

This groups exact final masked texts, not near-duplicate campaign families. Two messages with small wording changes may still be in different splits. So this is a leakage-aware first development split, not a campaign-independent test. A stronger evaluation later needs campaign/source grouping or a separately collected holdout.

The classes are imbalanced (legitimate 83.4%, scam 9.1%, spam 7.5%). Model evaluation must not rely on accuracy alone. Report precision, recall and F1 for each class, macro-F1 and a confusion matrix. A majority-class classifier can reach about 83.4% accuracy while missing all scam and spam examples.

Six unit tests were added in `backend/tests/test_create_mendeley_splits.py` for duplicate collapse, cross-label quarantine, stratification, reproducibility, no text leakage across splits and invalid input. The splitter and tests are committed but not yet run locally.


## 31. First real-data split generated

The user ran `python data\create_mendeley_splits.py` successfully.

Before splitting, the prepared derivative had 5,797 records. The splitter then:
- Grouped them into 5,722 unique normalised masked texts.
- Collapsed 36 same-label masked groups (74 prepared rows).
- Quarantined one cross-label masked-text group (2 prepared rows).
- Produced 5,721 final model rows.

### Final split counts

| Split | Total | Legitimate | Scam | Spam |
|---|---:|---:|---:|---:|
| Train | 4,004 | 3,383 | 318 | 303 |
| Validation | 856 | 724 | 68 | 64 |
| Test | 861 | 726 | 69 | 66 |

Integrity output confirmed that identical masked text does not cross splits and split groups remain in a single partition. The backend suite passed locally: `24 passed in 1.16s`.

**ML terms, simple Hinglish:**
- **Train:** Is data se model patterns seekhega.
- **Validation:** Model ya settings compare karne ke liye. Isse final test ko repeatedly touch karne ki zaroorat nahi.
- **Test:** Final unseen holdout. Iska result model tuning ke liye use nahi karna.
- **Stratified split:** Har class ko train/validation/test mein roughly same proportion mein rakhna.
- **TF-IDF:** Words aur word-pairs ko numerical values mein convert karta hai, taaki ML algorithm text ko process kar sake.
- **Logistic Regression:** Text ke learned weighted patterns ke basis par class scores/probabilities calculate karke category predict karta hai. Naam mein regression hai, lekin yahan classification ke liye use hota hai.

### Completed: install ML dependencies and run the fixed baseline

The requirements file now pins scikit-learn 1.9.1 and joblib 1.6.0. From the repository root, run:

```powershell
python -m pip install -r backend\requirements.txt
```

Then run the fixed first model:

```powershell
python data\train_text_baseline.py
```

The script fits the TF-IDF vocabulary and Logistic Regression only on the 4,004 training records. It reports validation metrics and the fixed initial test evaluation, then writes a model artifact and aggregate metric JSON under Git-ignored `data/private/model_artifacts/`.

Do not adjust the model based on the test results. Use validation for future changes and preserve test as an independent final holdout. Model artifact is joblib/pickle-based; only load the artifact generated by your own trusted run.

**Completed locally (11 November 2026):** The first baseline was trained and evaluated. Validation macro-F1: 0.8682; initial test macro-F1: 0.8915. Full backend suite: 31 passed in 4.54s. Keep test results out of future tuning decisions.


## 32. First ML baseline — TF-IDF + Logistic Regression

SOUL's first model will use two simple components:

### TF-IDF

TF-IDF means **Term Frequency–Inverse Document Frequency**.

Simple Hinglish: Ye text ke words ko numbers mein convert karta hai. Jo word ek message mein important hai, lekin har message mein common nahi hai, usko comparatively zyada weight mil sakta hai. Hum word unigrams aur bigrams use karenge:
- Unigram: one word, jaise "verify".
- Bigram: two consecutive words, jaise "verify account".

Vectorizer ko sirf training messages par fit karna hai. Validation/test data se vocabulary ya IDF weights learn nahi karne.

### Logistic Regression

Ye ek classification algorithm hai. Ye training examples se words ke weights seekhta hai aur message ke liye class scores calculate karta hai. SOUL mein possible classes:
- legitimate
- scam
- spam

`class_weight="balanced"` minority classes (scam and spam) ko training mein greater weight deta hai. Isse imbalance handle karne mein help mil sakti hai, lekin false positives bhi badh sakte hain. Metrics check karna zaroori hai.

### Fixed first recipe

- TF-IDF word unigrams + bigrams.
- `min_df=2`: training set mein ek hi message mein aane wale unique words drop ho sakte hain.
- Maximum 50,000 features.
- Logistic Regression with balanced class weights and 2,000 maximum iterations.
- Fixed seed 42.

### Evaluation

The first run reports validation and initial test metrics:
- Accuracy and balanced accuracy.
- Macro-F1 and weighted-F1.
- Per-class precision, recall, F1 and one-vs-rest false-positive rate.
- Confusion matrix.

A test set is not for tuning. Agar test output dekh kar hyperparameters/thresholds change karenge, test set independent final evaluation nahi rahega. Changes ke liye validation set use karo and test holdout ko preserve karo.

**Completed locally:** The model was trained. Validation metrics: accuracy 0.9638, balanced accuracy 0.8733, macro-F1 0.8682. Initial test metrics: accuracy 0.9675, balanced accuracy 0.8920, macro-F1 0.8915. Full suite: 39 passed in 5.16s. These are exploratory results, not real-world detection accuracy.

### Viva questions

**Q1. TF-IDF kya karta hai?**

Text ko numerical features mein convert karta hai, jisse machine-learning model words aur phrases ke patterns seekh sakta hai.

**Q2. Logistic Regression classification kaise karta hai?**

Training data se word weights learn karta hai and har class ke liye score calculate karta hai. Highest-scoring class prediction banti hai.

**Q3. Class imbalance kya hai?**

Jab ek class ke examples bahut zyada aur doosri classes ke examples kam hote hain. Hamare prepared data mein legitimate 83.4% hai, jabki scam 9.1% aur spam 7.5% hain.

**Q4. Accuracy alone kyun enough nahi hai?**

Har message ko legitimate bolne par bhi test split par roughly 84.3% accuracy aa sakti hai. Lekin model ek bhi scam ya spam catch nahi karega. Isliye per-class recall, macro-F1 aur confusion matrix dekhna zaroori hai.


## 33. Validation-only error analysis

Ab hum model ko change karne se pehle uski mistakes samjhenge.

- **Actual label:** Dataset mein message ki original class.
- **Predicted label:** Model ne jo class choose ki.
- **Misclassification:** Jab actual aur predicted label alag hon.
- **Top-class probability:** Model ke output ka highest class score. Isko guaranteed confidence ya fraud probability mat samajhna.

Run from the repository root:

```powershell
python data\analyze_baseline_errors.py
```

The script reads only the validation split, verifies that it is the exact split used in the baseline run, and does not retrain the model. It saves:
- Aggregate error counts in `validation_error_summary.json`.
- Message-level mistakes in `validation_misclassified.csv`.

Dono files `data/private/model_artifacts/` ke andar rahengi. Message-level CSV mein text hota hai; ise GitHub par commit, upload ya chat mein paste mat karna. Masking complete anonymity guarantee nahi karti. Sirf aggregate counts share karna.

**Next task:** Sabse common actual-to-predicted confusion identify karo. Abhi model settings change nahi karni; pehle examples ko locally inspect karke samajhna hai ki spam messages scam ya legitimate kyun predict ho rahe hain. Initial test split ko untouched rakho.


## 34. First validation error-analysis result

The validation-only script ran successfully and verified the saved validation split fingerprint. It did not read the initial test split and did not retrain the model.

- Validation messages: 856
- Correct predictions: 825
- Wrong predictions: 31
- Accuracy: 96.38%

Error pairs (actual → predicted):
- Spam → scam: 14
- Legitimate → spam: 7
- Scam → spam: 5
- Spam → legitimate: 5

**Simple Hinglish interpretation:** Model suspicious messages ko kaafi baar identify kar raha hai, lekin kuch spam ko scam samajh raha hai. Spam aur scam ka difference samajhne ke liye humein local examples dekhne honge. Abhi ye conclude nahi karna ki model ko kya confuse kar raha hai.

The message-level CSV is private. Review it on your own computer and classify each error into a broad reason (for example: promotional wording, urgency/impersonation wording, legitimate message with suspicious-looking terms, too little context, possible source-label ambiguity, masking removed useful clues, or unsure). A single message may fit more than one pattern; use one primary category consistently for a simple count. Do not paste message text into chat or GitHub. Share only category totals.

The new error-analysis utility has eight unit tests. The complete local test suite has now passed: 39 passed in 5.16s.


## 35. What the 31 validation mistakes actually show

I reviewed the uploaded misclassification report. The original message contents were not added to GitHub or to these notes.

| Actual → predicted | Count | Simple explanation |
|---|---:|---|
| Spam → scam | 14 | Prize offers, free gifts, premium-rate numbers, paid subscriptions and reward claims look scam-like. |
| Legitimate → spam | 7 | Some are short personal chats; others are service notifications or a genuine bank security warning. |
| Scam → spam | 5 | These examples look like commercial ads or service promotions, so they resemble spam. |
| Spam → legitimate | 5 | Some look like neutral service updates or normal conversations even though the source labels them spam. |

**Main finding:** 19/31 mistakes are between spam and scam. This is a class-definition problem we need to investigate, not a reason to immediately increase model complexity.

The source dataset's `smishing` label was mapped to `scam`. But a few examples in that class resemble normal commercial promotions or paid-service advertisements. We should keep the original source label separate from SOUL's own label and write a clear annotation rule before changing labels.

**Simple class distinction for the next annotation review:**
- **Spam:** Unsolicited promotion, marketing, bulk messages or premium-rate service advertising. It may be annoying or costly, but is not automatically phishing.
- **Scam/smishing:** A deceptive message that impersonates someone or tricks the recipient into revealing information, paying money, opening a malicious link or taking another harmful action.
- **Legitimate:** Expected personal, business, banking or service communication that is not deceptive or unsolicited promotion.

These are proposed SOUL annotation rules, not proof that every existing source label follows them.

**Next engineering decision:** Freeze this baseline, clarify labels and add representative hard-negative examples first. Do not tune against the test set, and do not automatically relabel the 19 spam/scam cases.


## 36. Validation error-analysis tests verified

After adding the eight tests for the validation-only error report, the complete backend test suite was run locally:

```text
39 passed in 5.16s
```

Iska matlab error-report ke helper functions aur pehle ke dataset/model helper tests sab pass hue. Ye software tests hain; ye model ki real-world fraud detection ability ka proof nahi hain.

**Next:** Dataset labels ko review karne se pehle source label aur SOUL label ko alag-alag record karne ka plan banayenge. Kisi source label ko sirf model prediction ke basis par change nahi karna.


## 37. Keep source labels separate from SOUL labels

We found that the source's `smishing` category does not always clearly match SOUL's `scam` definition. Isliye original publisher label ko overwrite nahi karenge.

Updated prepared-data fields:

- `source_label`: Mendeley ka original class — `ham`, `smishing`, `spam`.
- `label`: Purana provisional mapping, jo original baseline aur existing split mein use hua. Isko abhi change nahi karna.
- `soul_label`: Blank rahega jab tak human reviewer decision na le.
- `review_status`: Initially `pending`; review ke baad `reviewed` ya `needs_review`.
- `annotation_note`: Human decision ka short reason.

**Important:** Model ki prediction ko copy karke `soul_label` mat bharna. Model galat ho sakta hai; review independent hona chahiye.

The preparation code and validator have been updated, but local regeneration and verification are still pending. Existing train/validation/test files and the first model must remain unchanged.


## 38. Prepared dataset provenance validation completed

The updated preparation script was run locally. It retained all original aggregate counts:

- Source rows: 5,971.
- Prepared unique records: 5,797.
- Conflicting exact-text rows quarantined: 68.
- Provisional classes: legitimate 4,834, scam 528, spam 435.
- Original source classes: ham 4,834, smishing 528, spam 435.

The validator confirmed:
- 5,797 unique IDs and no blank text.
- Zero invalid source labels or provisional labels.
- Zero mismatches in the original source → provisional mapping.
- All 5,797 records have `review_status=pending`.
- Zero invalid SOUL labels or review-state inconsistencies.
- Zero residual matches for the known privacy regex patterns (this is not proof of anonymity).

The existing train/validation/test split and original model were not rebuilt. Full backend test suite: `45 passed in 5.25s`.

## 39. Next: blind review of validation mistakes

A new local helper creates two separate files from the 31 known validation errors:

- `validation_label_review_blind.csv`: contains the message and blank SOUL review fields, but hides original source labels and model predictions.
- `validation_label_review_key.csv`: contains source label, provisional label and model prediction, but no message text.

Run `python data\build_validation_label_review_queue.py` from the repository root after running the tests. Review the blind file first; do not open the key until independent labels are complete. This is an error-focused sample, not a representative sample of the dataset. Keep both files local and private.

The new queue builder has 12 unit tests. The previous 45-test result does not include these new tests; run the full suite again after pulling (expected 57 tests).


## 40. Assistant-assisted preliminary review of the 31 blind errors

I inspected the uploaded blind CSV without seeing its source-label/model-prediction key. Based only on the visible message text, I prepared an advisory suggestion sheet:

| Suggested SOUL category | Count |
|---|---:|
| Spam | 15 |
| Legitimate | 6 |
| Scam | 3 |
| Needs review | 7 |
| **Total** | **31** |

The delivered file is `validation_label_review_assistant_suggestions.csv`. It preserves the message text, adds `assistant_suggested_label` and `assistant_assessment_note`, and intentionally leaves `soul_label` blank, `review_status=pending`, and `annotation_note` blank.

**Important:** These are assistant-generated suggestions based only on short SMS text. They are not verified human labels or ground truth. Seven messages are too context-poor to classify responsibly. Some suggested `legitimate` or `scam` decisions are conditional on whether a service/registration was initiated by the recipient. A human reviewer should accept, edit or leave every suggestion pending.

The key containing original source labels and baseline predictions was not inspected. The 31 records were selected because the model misclassified them, so the counts must not be interpreted as class distribution or general dataset quality.

Do not train a new model from this suggestion sheet. Keep the initial baseline and test set frozen. The next comparison can happen only after human review and, separately, after the source/model key is intentionally opened to compare disagreements.
