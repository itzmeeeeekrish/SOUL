# SOUL – Learning Notes (Simple Hinglish)

Ye file tumhari revision notebook hai. Har naye module ke baad isme concept, code ka flow, testing aur viva questions add karenge.

> **Current status:** Project foundation documentation complete hai; application implementation abhi start nahi hui. Neeche diye concepts design ko samajhne ke liye hain; inka matlab ye nahi ki code implement ho chuka hai.

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
