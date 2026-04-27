from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from urllib.parse import urlparse
import requests
import tldextract
import socket
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
from utils import detect, email_scan_engine
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

def get_redirect_uri():
    # Automatically switch between localhost and production
    if request.host.startswith('localhost'):
        return "http://localhost:5000/oauth2callback"
    return f"https://{request.host}/oauth2callback"

# 🔥 IMPORT NEW ENGINE
from utils import detect

# -----------------------------
# 🔥 QR SESSION PERSISTENCE (VERCEL READY)
# -----------------------------
def set_qr_session(session_id, data):
    db.collection("qr_nodes").document(session_id).set({
        "data": data,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

def get_qr_session(session_id):
    doc = db.collection("qr_nodes").document(session_id).get()
    return doc.to_dict().get("data") if doc.exists else None

def update_qr_status(session_id, status, uid=None):
    ref = db.collection("qr_nodes").document(session_id)
    update = {"data.status": status}
    if uid: update["data.uid"] = uid
    ref.update(update)

# -----------------------------
# 🔥 OAUTH STATE PERSISTENCE (VERCEL READY)
# -----------------------------
import hashlib

def set_oauth_state(state, data):
    if not state: return
    try:
        # Hash the state to ensure a clean, path-safe Firestore ID
        safe_id = hashlib.sha256(state.encode()).hexdigest()
        
        db.collection("oauth_sessions").document(safe_id).set({
            "state": state,
            "data": data,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        print(f"🚀 [THREATX-CLOUD] Handshake Locked: {safe_id[:8]} (Actual: {state[:5]}...)")
    except Exception as e:
        print(f"❌ [THREATX-CLOUD] DB WRITE FAILED: {str(e)}")
        # Fallback to local log
        print(f"DANGER: State key {state[:5]} was not saved. Scan will fail.")

def get_oauth_state(state):
    if not state: return None
    try:
        safe_id = hashlib.sha256(state.encode()).hexdigest()
        print(f"🔍 [THREATX-CLOUD] Searching Handshake: {safe_id[:8]}...")

        # Try ID Pathway
        doc_ref = db.collection("oauth_sessions").document(safe_id)
        doc = doc_ref.get()
        if doc.exists:
            print("✅ [THREATX-CLOUD] Session Restored via ID")
            data = doc.to_dict().get("data")
            doc_ref.delete()
            return data

        # Try Query Pathway (Fallback)
        query = db.collection("oauth_sessions").where("state", "==", state).limit(1).stream()
        for doc in query:
            print("✅ [THREATX-CLOUD] Session Restored via Query")
            data = doc.to_dict().get("data")
            doc.reference.delete()
            return data
        
        print(f"❌ [THREATX-CLOUD] Security Token Not Found.")
        return None
    except Exception as e:
        print(f"❌ [THREATX-CLOUD] DB READ FAILED: {str(e)}")
        return None

def cleanup_oauth_state(state):
    try:
        db.collection("oauth_sessions").document(state).delete()
    except:
        pass

import json
# No local history file needed for production

# -----------------------------
# 🔥 FIRESTORE PERSISTENCE (VERCEL READY)
# -----------------------------
def get_user_history(user_id):
    try:
        docs = db.collection("history").where("user", "==", user_id).stream()
        h_list = []
        for d in docs:
            item = d.to_dict()
            # Ensure we capture both naming conventions for UI flexibility
            h_list.append({
                "url": item.get("url", "Unknown"),
                "score": item.get("score") if item.get("score") is not None else item.get("risk", 0),
                "status": item.get("status", "Unknown"),
                "timestamp": item.get("timestamp", ""),
                "reasons": item.get("reasons", [])
            })
        if h_list:
            # Fix: Handle None timestamps by using an empty string fallback during sort
            h_list.sort(key=lambda x: str(x.get("timestamp") or ""), reverse=True)
            print(f"📉 [THREATX-CLOUD] Retrieved {len(h_list)} history items from 'cybershield'")
            return h_list[:50]
    except Exception as e:
        print(f"❌ Cloud DB Error: {str(e)}")
    return []

def add_to_history(user_id, scan_data):
    try:
        from datetime import datetime
        scan_data["user"] = user_id
        if "timestamp" not in scan_data:
            scan_data["timestamp"] = datetime.utcnow().isoformat()
        db.collection("history").add(scan_data)
        print("✅ [THREATX-CLOUD] Logged to Cloud")
    except Exception as e:
        print(f"❌ [THREATX-CLOUD] Save Failed: {str(e)}")

# -----------------------------
# BASE DIR
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# -----------------------------
# FIREBASE ADMIN SETUP
# -----------------------------
firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
if firebase_json:
    import json
    service_account_info = json.loads(firebase_json)
    cred = credentials.Certificate(service_account_info)
else:
    cred_path = os.path.join(BASE_DIR, "serviceAccountKey.json")
    cred = credentials.Certificate(cred_path)

# Extract project ID automatically from service account
target_project_id = cred.project_id

firebase_admin.initialize_app(cred, {
    'storageBucket': f'{target_project_id}.appspot.com'
})

# Explicitly target your custom database 'cybershield'
try:
    db = firestore.client(database_id="cybershield")
    print("💎 [THREATX-CLOUD] Connected to database: 'cybershield'")
except:
    # Fallback to default if there is a version mismatch in firebase-admin
    db = firestore.client()

bucket = storage.bucket()

# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key-123")

app.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "fallback-secret-key-123"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_SAMESITE="Lax",   # 🔥 IMPORTANT
    PERMANENT_SESSION_LIFETIME=86400 * 30   # 30 days
)

# -----------------------------
# TRUSTED DOMAINS (FIXED)
# -----------------------------
trusted_domains = [
    "google.com",
    "firebaseapp.com",
    "github.com",
    "amazon.in",
    "microsoft.com",
    "youtube.com"
]

safe_words = ["meeting", "report", "project", "team", "schedule"]

# -----------------------------
# LOAD MODEL
# -----------------------------
try:
    model = pickle.load(open(os.path.join(BASE_DIR, "model.pkl"), "rb"))
    vectorizer = pickle.load(open(os.path.join(BASE_DIR, "vectorizer.pkl"), "rb"))
    print("✅ Model loaded")
except:
    print("⚠ Model not found")
    model = None
    vectorizer = None

# -----------------------------
# DOMAIN INFO
# -----------------------------
def get_domain_info(url):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc if parsed_url.netloc else parsed_url.path
        ip = socket.gethostbyname(domain)
        https = url.startswith("https")
        return {"ip": ip, "https": https}
    except:
        return {"ip": "Unknown", "https": False}

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/login")
def login():
    if session.get("user"):
        return redirect("/")
    return render_template("login.html")

@app.route("/create-qr-session")
def create_qr():
    session_id = str(uuid.uuid4())
    set_qr_session(session_id, {"status": "pending"})
    return jsonify({"session_id": session_id})

@app.route("/check-qr/<session_id>")
def check_qr(session_id):
    session_data = get_qr_session(session_id)
    return jsonify(session_data if session_data else {"status": "invalid"})

@app.route("/qr-login-complete", methods=["POST"])
def qr_login_complete():
    session_id = request.json.get("session_id")
    uid = request.json.get("uid")

    if session_id:
        # Update the cloud record so the desktop can see the success
        update_qr_status(session_id, "success", uid)
        session.permanent = True
        session["user"] = uid

    return jsonify({"success": True})

@app.route("/mobile-auth/<session_id>")
def mobile_auth(session_id):
    return render_template("mobile.html", session_id=session_id)


@app.route("/passkey-auth", methods=["POST"])
def passkey_auth():
    session.permanent = True
    session["user"] = "SecureHQ_Passkey_Agent"
    session["user_email"] = "passkey-simulated@aegis.local"
    return jsonify({"success": True})


@app.route("/scan-emails", methods=["POST"])
def scan_emails():
    # Check user login/session
    if not session.get("user"):
        return jsonify({"status":"Unauthorized", "risk":0, "reasons":["Login required"]})

    # -----------------------
    # 🔥 Dummy scan (replace with Gmail API)
    emails = [
        "Your account suspended click here",
        "Welcome to Amazon",
        "Free prize, click to claim"
    ]
    threats = [e for e in emails if "click" in e.lower()]

    return jsonify({
        "status": "Danger" if threats else "Safe",
        "risk": len(threats) * 30,  # dummy risk %
        "reasons": threats
    })

# -----------------------------
# GOOGLE VERIFY
# -----------------------------
@app.route("/verify-google", methods=["POST"])
def verify_google():
    id_token = request.json.get("idToken")
    try:
        decoded = auth.verify_id_token(id_token)
        session.permanent = True
        session["user"] = decoded["uid"]
        session["user_email"] = decoded.get("email", "Google OAuth Agent")
        return jsonify({"success": True})
    except:
        return jsonify({"success": False})
    

@app.route("/verify-email", methods=["POST"])
def verify_email():
    id_token = request.json.get("idToken")
    try:
        decoded = auth.verify_id_token(id_token)
        session.permanent = True
        session["user"] = decoded["uid"]
        session["user_email"] = decoded.get("email", "Email Credentials Agent")
        return jsonify({"success": True})
    except:
        return jsonify({"success": False})
    
@app.route("/gmail-login")
def gmail_login():
    google_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if google_json:
        import json
        client_config = json.loads(google_json)
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=get_redirect_uri()
        )
    else:
        flow = Flow.from_client_secrets_file(
            os.path.join(BASE_DIR, "credentials.json"),
            scopes=SCOPES,
            redirect_uri=get_redirect_uri()
        )

    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )

    # HYBRID STORAGE: Cloud + Local Session Backup
    user_id = session.get("user")
    state_data = {
        'code_verifier': getattr(flow, 'code_verifier', None),
        'user': user_id
    }
    set_oauth_state(state, state_data)
    
    # Backup in session
    session['oauth_state'] = state
    session[f'state_data_{state}'] = state_data
    
    return redirect(auth_url)

@app.route("/oauth2callback")
def callback():
    # Attempt to grab state from request args directly
    state = request.args.get('state')
    
    if not state:
        print("❌ State missing from Google callback request.")
        return "Authentication Interrupted: Google did not return a security token. Please try again.", 400

    print(f"✅ Callback received for state: {state[:8]}...")

    google_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if google_json:
        import json
        client_config = json.loads(google_json)
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            state=state,
            redirect_uri=get_redirect_uri()
        )
    else:
        flow = Flow.from_client_secrets_file(
            os.path.join(BASE_DIR, "credentials.json"),
            scopes=SCOPES,
            state=state,
            redirect_uri=get_redirect_uri()
        )

    # PATHWAY 1: Try Local Session (Fastest)
    stored_data = session.get(f'state_data_{state}')
    
    # PATHWAY 2: Try Cloud Database (Resilient for Vercel)
    if not stored_data:
        print(f"🔄 Session fallback to cloud for state: {state[:8]}...")
        stored_data = get_oauth_state(state)

    if not stored_data:
        # Final error for user
        return f"Authentication Session Expired (State Key: {state[:5]}...). Please return to the dashboard and try scanning again.", 400

    flow.code_verifier = stored_data.get('code_verifier')

    # Forcefully restore user session
    restored_user = stored_data.get('user')
    if restored_user:
        session.permanent = True
        session["user"] = restored_user

    try:
        flow.fetch_token(authorization_response=request.url)
        # Success! Now cleanup the state
        cleanup_oauth_state(state)
    except Exception as e:
        print("Token fetch error:", e)
        return f"Verification Failed: {str(e)}. Ensure your Google App status is 'In Production' or you are a registered Test User.", 400

    creds = flow.credentials
    session['gmail_creds'] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes)
    }
    session.pop('oauth_state', None)

    # Return directly to the scanner with auto-run parameter
    return redirect("/?auto_scan=true")

@app.route("/email-scan", methods=["POST"])
def email_scan():

    if "gmail_creds" not in session:
        return jsonify({
            "risk": 0,
            "status": "Login required",
            "reasons": ["Please login with Gmail"]
        })

    creds = Credentials(**session['gmail_creds'])
    service = build('gmail', 'v1', credentials=creds)

    scanned_email = "Unknown"
    try:
        profile = service.users().getProfile(userId='me').execute()
        scanned_email = profile.get("emailAddress", "Unknown")
        print(f"📧 [THREATX-GMAIL] Scanning Inbox: {scanned_email}")
    except Exception as e:
        print(f"❌ [THREATX-GMAIL] Profile Fetch Failed: {str(e)}")
        # Fallback: check if we have it in session from a previous login
        scanned_email = session.get("user_email", "Unknown")

    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])

    highest_score = 0
    all_reasons = []
    
    safe_count = 0
    suspicious_count = 0
    danger_count = 0

    for msg in messages:
        try:
            m = service.users().messages().get(userId='me', id=msg['id']).execute()
            snippet = m.get("snippet", "")
            if not snippet: continue

            score, status, reasons = email_scan_engine(snippet)

            if score > highest_score:
                highest_score = score
                
            if score >= 70:
                danger_count += 1
            elif score >= 40:
                suspicious_count += 1
            else:
                safe_count += 1

            for r in reasons:
                if r not in all_reasons:
                    all_reasons.append(r)
        except Exception:
            continue

    final_score = min(highest_score, 100)

    if final_score >= 70:
        final_status = "Danger"
    elif final_score >= 40:
        final_status = "Suspicious"
    else:
        final_status = "Safe"

    # Save to Cloud Firestore
    user = session.get("user")
    from datetime import datetime
    if user:
        add_to_history(user, {
            "url": f"Gmail Scan ({scanned_email})",
            "risk": final_score,
            "status": final_status,
            "timestamp": datetime.utcnow().isoformat()
        })

    return jsonify({
        "risk": final_score,
        "status": final_status,
        "scanned_email": scanned_email,
        "safe_count": safe_count,
        "suspicious_count": suspicious_count,
        "danger_count": danger_count,
        "reasons": all_reasons[:10]
    })


@app.route("/disconnect-gmail", methods=["POST"])
def disconnect_gmail():
    # Flushes existing OAuth tokens independently directly out of memory allowing cleanly linking a new inbox
    session.pop('gmail_creds', None)
    return jsonify({"success": True})

# -----------------------------
# LOGOUT / HOME
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/")
def home():
    if not session.get("user"):
        return redirect("/login")
    return render_template("index.html")

# -----------------------------
# USER META INFO
# -----------------------------
@app.route("/get_user_info")
def get_user_info():
    return jsonify({
        "uid": session.get("user", "Unknown"),
        "email": session.get("user_email", "Manual / Missing Credentials Context")
    })

# -----------------------------
# HISTORY
# -----------------------------
@app.route("/get_history")
def get_history():
    user = session.get("user")
    if not user: return jsonify([])
    
    try:
        # Force sort-by-Python for perfect reliability
        user_hist = get_user_history(user)
        return jsonify(user_hist or [])
    except Exception as e:
        print(f"⚠️ [THREATX-RESILIENCE] History Fetch Error: {e}")
        return jsonify([])

@app.route("/clear_history", methods=["POST"])
def clear_history():
    user = session.get("user")
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        batch = db.batch()
        docs = db.collection("history").where("user", "==", user).stream()
        for doc in docs:
            batch.delete(doc.reference)
        batch.commit()
    except Exception as e:
        print(f"❌ Cloud Clear Failed: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True})


# -----------------------------
# 🔥 FINAL PREDICT (BALANCED + FIXED)
# -----------------------------
@app.route("/predict", methods=["POST"])
def predict():
    if not session.get("user"):
        return jsonify({"score": 0, "status": "Unauthorized"}), 401

    data = request.get_json()
    text = data.get("text", "").strip()
    url = data.get("url", "").strip()

    score = 0
    reasons = []

    if url:
        result = detect(url, text)
        score = result["score"]
        reasons.extend(result["reasons"])
    elif text:
        from utils import analyze_msg
        m_score, m_r = analyze_msg(text)
        score += m_score
        reasons.extend(m_r)

    if model and vectorizer and text:
        text_vec = vectorizer.transform([text])
        proba = model.predict_proba(text_vec)[0][1]
        if proba > 0.75:
            score += 20
            reasons.append("AI strongly detects phishing patterns")

    if url and check_phishtank(url):
        score += 30
        reasons.append("Reported phishing (PhishTank Database)")

    risk = int(max(0, min(score, 100)))
    status = "PHISHING" if risk >= 70 else "SUSPICIOUS" if risk >= 40 else "SAFE"

    user = session.get("user")
    if user:
        add_to_history(user, {
            "url": url if url else "Text Analysis",
            "msg": text[:50],
            "score": risk,
            "status": status,
            "reasons": list(set(reasons))
        })

    # Get domain info for UI
    domain_info = get_domain_info(url) if url else {"ip": "N/A", "https": False}

    return jsonify({
        "score": risk,
        "status": status,
        "reasons": list(set(reasons)),
        "ip": domain_info["ip"],
        "https": domain_info["https"]
    })

# -----------------------------
# PHISHTANK
# -----------------------------
def check_phishtank(url):
    try:
        res = requests.post("http://checkurl.phishtank.com/checkurl/", data={"url": url})
        return '"in_database":true' in res.text.lower()
    except:
        return False

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)