# SOUL Message Annotation Guide

**Version:** 0.1  
**Applies to:** SMS/message text examples in Milestone 2.

## Goal

Assign labels according to the message's apparent intent and requested action—not simply because it contains a link, mentions a bank, uses urgent language, or is written in poor grammar.

The three model labels are:

- `legitimate`
- `spam`
- `scam`

If there is not enough context to make a defensible decision, mark the item `needs_review` in the annotation working notes and do not add it to the final labelled CSV until reviewed. `needs_review` is not a model class in the current three-class baseline.

## 1. Legitimate

Use `legitimate` for ordinary, expected or benign communication.

Examples:
- A payment receipt or transaction alert that does not ask the user to reveal secrets.
- A delivery or appointment update.
- A normal conversation.
- A login OTP message that explicitly says not to share the code.

A message does not become a scam merely because it mentions money, a bank, an OTP, or a URL. Consider the full context and requested action.

## 2. Spam

Use `spam` for unsolicited or unwanted promotional/junk messages that advertise products, services, events or offers, without a clear attempt to deceive the recipient into handing over money, credentials or control of a device/account.

Examples:
- A restaurant discount advertisement.
- A coaching-centre course promotion.
- A general retail sale announcement.

Spam can be annoying and unwanted without being fraud. Do not automatically label all promotional messages as scams.

## 3. Scam

Use `scam` when the message appears designed to deceive or manipulate the recipient for financial gain, sensitive information, account access or device control.

Common indicators include:
- Impersonating a bank, government department, courier, employer, family member or another trusted party.
- Threatening account closure, service disconnection or legal trouble to force immediate action.
- Asking for OTPs, PINs, passwords, recovery codes or remote access.
- Asking the recipient to approve a UPI collect request or transfer money under false pretences.
- Demanding an upfront fee to receive a prize, job, loan or guaranteed investment return.
- Directing the user to a deceptive or unverified payment/login destination.

The presence of one indicator should be assessed in context. A risk indicator is not automatically proof that the sender is malicious.

## Decision order

1. **What action does the message ask the recipient to take?** Read the whole message.
2. **Is there an apparent deception or impersonation?** Identify the claim and who the sender pretends to be.
3. **Is the recipient being asked for money, secrets, account access or a risky action?**
4. **If it is only promotion without deceptive pressure or sensitive-data collection, prefer spam.**
5. **If it is ordinary or expected communication without harmful intent, prefer legitimate.**
6. **If intent cannot be established from the available text, send it for review instead of guessing.**

## Important edge cases

| Situation | Preferred treatment |
|---|---|
| Normal bank debit notification with masked account details and no request for secrets | Legitimate, assuming the example is a genuine/expected notification |
| Promotional message with a discount and no deceptive request | Spam |
| Message claiming a bank account will be blocked unless the user enters an OTP on an unverified page | Scam |
| Message contains a URL but the surrounding context is neutral | Do not label scam based on URL presence alone; review the destination separately |
| Urgent language without a suspicious request or deception | Not enough by itself to call it a scam |
| Unknown sender or unfamiliar number alone | Not enough by itself to call it a scam |
| Message asks the user to share a PIN/OTP or approve a payment under a false pretext | Scam |
| Ambiguous marketing/loan offer with missing context | Needs review |

## Consistency and review

- Use the same rules for English, Hindi and Hinglish.
- Do not infer a label from language, spelling quality, sender identity, or brand name alone.
- Keep a short `annotation_note` explaining the deciding evidence.
- Borderline examples should be reviewed by a second annotator before inclusion in an evaluation set.
- When reviewers disagree, record the disagreement and revise the guide; do not silently force a label.
- Never include unmasked personal or financial information in examples.

## Starter dataset note

The 24 rows in `data/synthetic/sms_messages.csv` are hand-authored educational examples. They are deliberately balanced across the three labels and should not be treated as a representative sample of real incoming messages or used to claim production accuracy.
