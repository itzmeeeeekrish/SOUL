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

