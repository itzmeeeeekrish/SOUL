# SOUL – Learning Notes (Simple Hinglish)

Ye file tumhari revision notebook hai. Har naye module ke baad isme concept, code ka flow, testing aur viva questions add karenge.

> **Current status:** Repository aur backend foundation complete hain. 10 November 2026 ko local API run hua, /health browser mein verify hua aur pytest mein 1 test bina warning ke pass hua. Milestone 2 mein dataset schema, annotation guide aur 24 synthetic message examples add kiye gaye hain. Real public datasets abhi import nahi hue.

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
