# Security Policy

Thank you for helping keep **ThreatX** secure. We take security vulnerabilities very seriously. If you discover a security vulnerability in this project, we appreciate your help in disclosing it to us in a responsible manner.

This document outlines our security policies, supported versions, and the process for reporting vulnerabilities.

---

## Supported Versions

We actively maintain and support security updates for the following versions of ThreatX:

| Version | Supported | Notes |
| ------- | --------- | ----- |
| `main` (branch) |  Active | Current development and release branch. |
| `< 1.0.0` |  End of Life | Older development releases. Please upgrade to the latest commit on `main`. |

We recommend always running the latest code from the `main` branch to ensure you have all security patches and dependency updates.

---

## Reporting a Vulnerability

**Do NOT open a public GitHub issue** for security vulnerabilities. Doing so exposes the vulnerability publicly before a patch can be developed and deployed, which could put users at risk.

Instead, please report security vulnerabilities using one of the following methods:

1. **GitHub Security Advisory (Recommended)**: Go to the **Security** tab of this repository on GitHub, click on **Advisories**, and select **Report a vulnerability** to submit a private report.
2. **Direct Email**: Send a detailed email to **omkarmahadik96@gmail.com** (or your preferred contact email).
   * *If the vulnerability is extremely sensitive, please encrypt your email using a PGP key (if available) or request a secure communication channel in your initial email.*

### What to Include in a Report
To help us triage and resolve the issue quickly, please include as much of the following information as possible:
* **Description**: A clear summary of the vulnerability and its potential impact.
* **Steps to Reproduce**: Detailed step-by-step instructions (and code snippets, payloads, or screenshots if applicable) to reproduce the behavior.
* **Component Affected**: Specify the affected component (e.g., Flask backend, OAuth callback flow, Firestore state synchronization, extension, etc.).
* **Suggested Fix**: If you have a potential patch or mitigation strategy, please share it.

---

## Our Security Response Process

Once a vulnerability report is received, we will follow these steps to address it:

1. **Acknowledgment**: We will acknowledge receipt of your report within **48 hours** and confirm whether we can reproduce the issue.
2. **Triage & Assessment**: We will evaluate the severity of the vulnerability (using CVSS guidelines where applicable) and its impact on the system.
3. **Patch Development**: We will work on a fix. We may contact you for further details or to test the patch.
4. **Coordinated Disclosure**: We will publish a security patch on the `main` branch and, if applicable, coordinate a public disclosure/advisory to inform other users of the fix. We aim to resolve and disclose vulnerabilities within **30 to 90 days** of receipt, depending on complexity.

---

## 🔒 Security Best Practices for ThreatX Deployers

ThreatX handles sensitive permissions (such as Google OAuth `gmail.readonly` and Firebase Service Account access). To keep your deployment secure, please adhere to the following best practices:

### 1. Secret Key & Environment Variable Safety
* **Never commit secrets**: Never commit your `.env`, `serviceAccountKey.json`, or OAuth credentials to public repositories. Ensure they are listed in your `.gitignore`.
* **Strong Secret Key**: Ensure `FLASK_SECRET_KEY` is a cryptographically strong, random string (e.g., generated using `secrets.token_hex(32)`).
* **Production Variables**: In production hosting environments (e.g., Vercel, Heroku, AWS), inject these secrets as environment variables through the hosting platform's dashboard rather than storing them in files.

### 2. Firestore Security Rules
Because ThreatX uses Firestore (`cybershield` database) to coordinate passwordless QR biometric sync and OAuth states, configure strong security rules. Do not allow public write or read access to all collections.
Example Firestore rule guideline:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Only allow operations on qr_nodes and oauth_sessions under strict validation or backend-only (Admin SDK)
    match /qr_nodes/{sessionId} {
      allow read, write: if true; // Restrict this to authenticated user IDs or validated states in production
    }
    match /oauth_sessions/{sessionId} {
      allow read, write: if false; // Only accessible via Firebase Admin SDK backend
    }
  }
}
