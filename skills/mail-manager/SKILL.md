---
name: mail-manager
description: "Checks incoming emails and sends messages via standard IMAP/SMTP (Gmail App Password, Outlook, custom mailboxes)."
version: 1.0.0
author: Emanuel Gössler
tags: [groundsole, email, mail, gmail, inbox, send]
---

# Mail Manager Skill

This skill enables the AI coprocessor to check new emails in the user's inbox and draft or send emails on behalf of the user.

---

## Trigger Conditions

Activate this skill when:
- The user requests: *"Check my emails"*, *"Are there new messages in my inbox?"*, *"Send an email to..."*, or *"Mailbox checken"*.

---

## 🛠️ Execution Commands

### 1. Check Inbox
Retrieves the latest unread emails:
```bash
python3 scripts/mail_helper.py check [limit]
```

### 2. Send Email
Sends a plain text message via SMTP:
```bash
python3 scripts/mail_helper.py send <recipient@domain.com> "<Subject>" "<Body text>"
```

---

## 🔒 Security & Privacy
- Credentials must be stored locally in `credentials.json` (outside Git tracking).
- For Gmail: Use a 16-letter **Google App Password** (from Google Account ➔ Security ➔ 2-Step Verification ➔ App Passwords). Never use your primary master account password.
