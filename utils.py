import requests
import tldextract
import ssl
import socket
import re
import base64

# -----------------------------
# 🔥 DOMAIN ANALYSIS (RISK SCORING)
# -----------------------------
def check_domain(url):
    ext = tldextract.extract(url)
    base_domain = ext.domain + "." + ext.suffix
    full_domain = ".".join(part for part in [ext.subdomain, ext.domain, ext.suffix] if part)

    risk_score = 0
    reasons = []

    TRUSTED = [
        "google.com", "firebaseapp.com", "amazon.in", "googleapis.com", 
        "gmail.com", "amazon.com", "github.com", "microsoft.com", 
        "facebook.com", "paypal.com", "netflix.com"
    ]

    # ✅ DIRECT MATCH (Reduce Risk)
    if base_domain in TRUSTED:
        risk_score -= 40
        reasons.append("Trusted base domain")
    # ✅ SUBDOMAIN OF TRUSTED (Reduce Risk)
    elif any(base_domain.endswith("." + td) for td in TRUSTED):
        risk_score -= 30
        reasons.append("Trusted subdomain ecosystem")
    # No arbitrary penalty for regular domains

    # 🔴 fake lookalike
    if re.search(r'(g00gle|gooogle|amaz0n|paypa1)', base_domain):
        risk_score += 50
        reasons.append("Fake lookalike domain detected")

    # 🔴 numbers
    if re.search(r'\d', ext.domain):
        risk_score += 15
        reasons.append("Numbers in domain name")

    # 🔴 hyphen
    if "-" in ext.domain:
        risk_score += 10
        reasons.append("Hyphenated domain Name")

    # 🔴 long domain
    if len(full_domain) > 30:
        risk_score += 15
        reasons.append("Suspiciously long domain")

    return risk_score, reasons

# -----------------------------
# 🔥 WEBSITE REACHABILITY
# -----------------------------
def check_website(url):
    try:
        r = requests.get(url, timeout=5, allow_redirects=True)
        if r.status_code == 200:
            return -10, ["Website is live and reachable"]
        return +15, [f"Website returned error: {r.status_code}"]
    except:
        return +25, ["Website is unreachable / Invalid DNS"]

# -----------------------------
# 🔥 SSL CHECK
# -----------------------------
def check_ssl(url):
    try:
        domain = url.split("//")[-1].split("/")[0]
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(3)
            s.connect((domain, 443))
        return -20, ["Valid SSL Certificate"]
    except:
        return +30, ["Missing or Invalid SSL Certificate"]

# -----------------------------
# 🔥 URL PATTERN CHECK
# -----------------------------
def check_url_pattern(url):
    risk_score = 0
    reasons = []

    # IP in URL
    if re.search(r'https?://\d+\.\d+\.\d+\.\d+', url):
        risk_score += 40
        reasons.append("IP address explicitly used in URL")

    # @ symbol
    if "@" in url:
        risk_score += 30
        reasons.append("@ symbol obfuscation in URL")

    # multiple //
    if url.count("//") > 1:
        risk_score += 15
        reasons.append("Multiple redirects or // patterns")

    return risk_score, reasons

# -----------------------------
# 🔥 MESSAGE ANALYSIS
# -----------------------------
def analyze_msg(msg):
    risk_score = 0
    reasons = []

    if not msg:
        return risk_score, reasons

    danger_words = ["urgent", "verify", "login", "otp", "password", "bank", "click", "suspend", "action required"]

    hits = 0
    for w in danger_words:
        if w in msg.lower():
            hits += 1
            reasons.append(f"Suspicious Action Keyword: '{w}'")
    
    if hits >= 3:
        risk_score += 25
    elif hits > 0:
        risk_score += 10

    if msg.isupper() and len(msg) > 10:
        risk_score += 10
        reasons.append("All CAPS message (High Urgency)")

    return risk_score, reasons

# -----------------------------
# 🔥 VIRUSTOTAL API
# -----------------------------
def check_virustotal(url):
    try:
        API_KEY = "98dcc4ea40e32eee7099774f27cd5e7d013dcb196e31850cf5a53ae96324ed4a"
        headers = {"x-apikey": API_KEY}
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")

        res = requests.get(f"https://www.virustotal.com/api/v3/urls/{url_id}", headers=headers)
        if res.status_code != 200:
            return 0, []

        data = res.json()
        stats = data["data"]["attributes"]["last_analysis_stats"]
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)

        if malicious > 0:
            return +60, [f"VirusTotal Alert: {malicious} security vendors flagged as malicious"]
        elif suspicious > 0:
            return +30, [f"VirusTotal Warning: {suspicious} security vendors flagged as suspicious"]
        else:
            return -20, ["VirusTotal: Clean across all security vendors"]

    except Exception as e:
        return 0, ["VirusTotal scan skipped (Timeout or Error)"]

# -----------------------------
# 🔥 FINAL DETECT ENGINE
# -----------------------------
def detect(url, msg=""):
    total_risk = 0  # 0 means completely safe
    reasons = []

    vt_risk, vt_reasons = check_virustotal(url)
    total_risk += vt_risk
    reasons.extend(vt_reasons)

    # Short Circuit for explicitly trusted VT clean with major domain
    trusted_base = ["google.com", "gmail.com", "github.com", "amazon.com", "microsoft.com"]
    if vt_risk == -20 and any(td in url for td in trusted_base):
        return {"score": 0, "status": "SAFE", "reasons": ["Trusted Authority Domain (Verified)"]}

    d_risk, d_r = check_domain(url)
    total_risk += d_risk
    reasons.extend(d_r)

    w_risk, w_r = check_website(url)
    total_risk += w_risk
    reasons.extend(w_r)

    s_risk, s_r = check_ssl(url)
    total_risk += s_risk
    reasons.extend(s_r)

    u_risk, u_r = check_url_pattern(url)
    total_risk += u_risk
    reasons.extend(u_r)

    m_risk, m_r = analyze_msg(msg)
    total_risk += m_risk
    reasons.extend(m_r)

    # Normalization (0 to 100)
    final_score = max(0, min(100, total_risk))

    if final_score >= 70:
        status = "PHISHING"
    elif final_score >= 40:
        status = "SUSPICIOUS"
    else:
        status = "SAFE"

    # Filter out empty or duplicate reasons
    unique_reasons = list(dict.fromkeys([r for r in reasons if r]))

    return {
        "score": final_score,
        "status": status,
        "reasons": unique_reasons
    }

# -----------------------------
# 📧 EMAIL API SCAN ENGINE
# -----------------------------
def email_scan_engine(text):
    risk_score, reasons = analyze_msg(text)
    
    urls = re.findall(r'https?://\S+', text)
    for u in urls:
        risk_score += 15
        reasons.append(f"Contains Embedded URL: {u}")
        # Run deeper url scan if desired, but for speed we just flag it
        p_res = detect(u)
        risk_score += (p_res["score"] * 0.5)
        reasons.extend(p_res["reasons"])

    final_score = max(0, min(100, int(risk_score)))

    if final_score >= 70:
        status = "PHISHING"
    elif final_score >= 40:
        status = "SUSPICIOUS"
    else:
        status = "SAFE"

    # dedupe
    reasons = list(dict.fromkeys(reasons))

    return final_score, status, reasons