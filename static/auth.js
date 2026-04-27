import { initializeApp } from "https://www.gstatic.com/firebasejs/12.11.0/firebase-app.js";
import { 
    getAuth, GoogleAuthProvider, signInWithPopup, 
    createUserWithEmailAndPassword, signInWithEmailAndPassword,
    sendEmailVerification, sendPasswordResetEmail
} from "https://www.gstatic.com/firebasejs/12.11.0/firebase-auth.js";

// Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyDe3Rc10Sn8cgS5hZ0Y6V0yFbcG6ahrOMg",
  authDomain: "cybershield-ai-a5d7b.firebaseapp.com",
  projectId: "cybershield-ai-a5d7b",
  storageBucket: "cybershield-ai-a5d7b.appspot.com",
  messagingSenderId: "121640241217",
  appId: "1:121640241217:web:d2a9c975c435dcae5cdec0"
};

// INIT
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

// ================= UI HELPERS =================
function showError(message) {
    const errDiv = document.getElementById("errorMessage");
    const errText = document.getElementById("errorText");
    
    // Provide specific guidance for common Firebase errors
    if (message.includes("auth/unauthorized-domain")) {
        message = "Domain Unauthorized: Add 'localhost' to your Firebase Console -> Authentication -> Settings -> Authorized domains.";
    }

    if(errDiv && errText) {
        errText.innerText = message;
        errDiv.style.display = "block";
        errDiv.style.animation = "shake 0.4s ease-in-out";
    }
    showPopup(message, "error");
}

function hideError() {
    const errDiv = document.getElementById("errorMessage");
    if(errDiv) errDiv.style.display = "none";
}

// ================= POPUP =================
function showPopup(message, type="info"){

    const popup = document.createElement("div");
    popup.innerText = message;

    // base style
    popup.style.position = "fixed";
    popup.style.top = "25px";
    popup.style.right = "25px";
    popup.style.padding = "14px 22px";
    popup.style.borderRadius = "12px";
    popup.style.color = "#fff";
    popup.style.fontSize = "14px";
    popup.style.fontWeight = "500";
    popup.style.zIndex = "9999";
    popup.style.opacity = "0";
    popup.style.transform = "translateX(120%) scale(0.9)";
    popup.style.transition = "all 0.5s cubic-bezier(.22,1,.36,1)";
    popup.style.backdropFilter = "blur(12px)";
    popup.style.border = "1px solid rgba(255,255,255,0.1)";
    popup.style.letterSpacing = "0.3px";

    // ICON + COLOR
    let icon = "ℹ";
    let glow = "0 0 20px rgba(0,255,255,0.2)";

    if(type === "success"){
        popup.style.background = "linear-gradient(135deg,#00ffcc,#00c851)";
        icon = "✅";
        glow = "0 0 25px rgba(0,255,150,0.4)";
    }
    else if(type === "error"){
        popup.style.background = "linear-gradient(135deg,#ff4b4b,#cc0000)";
        icon = "❌";
        glow = "0 0 25px rgba(255,0,0,0.4)";
    }
    else if(type === "warning"){
        popup.style.background = "linear-gradient(135deg,#ffbb33,#ff8800)";
        icon = "⚠";
        glow = "0 0 25px rgba(255,165,0,0.4)";
    }
    else{
        popup.style.background = "rgba(40,40,40,0.8)";
        icon = "ℹ";
    }

    popup.style.boxShadow = glow;

    // content with icon
    popup.innerHTML = `<span style="margin-right:8px">${icon}</span>${message}`;

    document.body.appendChild(popup);

    // ENTER animation
    setTimeout(()=>{
        popup.style.opacity = "1";
        popup.style.transform = "translateX(0) scale(1)";
    },100);

    // EXIT animation
    setTimeout(()=>{
        popup.style.opacity = "0";
        popup.style.transform = "translateX(120%) scale(0.9)";
        setTimeout(()=> popup.remove(),500);
    },3200);
}

// ================= VALIDATION =================
function isValidEmail(email){
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isStrongPassword(password){
    return password.length >= 6;
}

// ================= GOOGLE LOGIN =================
document.getElementById("googleSignInBtn").addEventListener("click", async ()=>{
    hideError();
    try{
        const result = await signInWithPopup(auth, provider);
        const idToken = await result.user.getIdToken();

        const resp = await fetch("/verify-google",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body: JSON.stringify({idToken})
        });

        const data = await resp.json();

        if(data.success){
            if(window.triggerWelcome) window.triggerWelcome(result.user.displayName || "Google User");
            else setTimeout(()=> window.location.href="/", 800);
        }else{
            showError(data.error || "Server rejected Google authentication.");
        }

    }catch(err){
        console.error("Google Auth Error:", err);
        showError(err.message || "Google login failed");
    }
});

// ================= EMAIL LOGIN =================
document.getElementById("emailLoginBtn").addEventListener("click", async ()=>{
    hideError();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if(!email || !password){
        showPopup("Enter email & password","error");
        return;
    }

    if(!isValidEmail(email)){
        showPopup("Invalid email","error");
        return;
    }

    try{
        const userCredential = await signInWithEmailAndPassword(auth,email,password);

        if(!userCredential.user.emailVerified){
            showPopup("Verify your email first","error");
            return;
        }

        const idToken = await userCredential.user.getIdToken();

        const resp = await fetch("/verify-email",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({idToken})
        });

        const data = await resp.json();

        if(data.success){
            if(window.triggerWelcome) window.triggerWelcome(userCredential.user.email);
            else setTimeout(()=> window.location.href="/",800);
        }else{
            showError("Login failed");
        }

    }catch(err){
        console.error("Email Login Error:", err);
        showError(err.message || "Login error");
    }
});

// ================= REGISTER =================
document.getElementById("emailRegisterBtn").addEventListener("click", async ()=>{

    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value.trim();

    if(!email || !password){
        showPopup("All fields required","error");
        return;
    }

    if(!isValidEmail(email)){
        showPopup("Invalid email","error");
        return;
    }

    if(!isStrongPassword(password)){
        showPopup("Password min 6 chars","error");
        return;
    }

    try{
        const userCredential = await createUserWithEmailAndPassword(auth,email,password);

        await sendEmailVerification(userCredential.user);

        showPopup("Verification email sent 📩","success");

        setTimeout(()=>{
            window.location.href="/verify-email-page";
        },1500);

    }catch(err){
        showPopup("Registration failed","error");
    }
});

// ================= FORGOT PASSWORD =================
const forgotBtn = document.getElementById("forgotPasswordBtn");
if(forgotBtn){
    forgotBtn.addEventListener("click", async ()=>{
        const email = document.getElementById("email").value.trim();

        if(!email){
            showPopup("Enter email first","error");
            return;
        }

        try{
            await sendPasswordResetEmail(auth,email);
            showPopup("Reset email sent","success");
        }catch{
            showPopup("Reset failed","error");
        }
    });
}

// ================= QR PASSKEY LOGIN =================
document.getElementById("passkeyBtn").addEventListener("click", async ()=>{

    const qrBox = document.getElementById("qrContainer");
    const qrImg = document.getElementById("qrImage");
    const qrStatus = document.getElementById("qrStatus");

    // show box
    qrBox.style.display = "block";
    qrBox.style.animation = "pulseGlow 2s infinite";

    qrStatus.innerText = "Generating secure QR...";

    try{
        const resp = await fetch("/create-qr-session");
        const data = await resp.json();

        const sessionId = data.session_id;

        // 👉 IMPORTANT: replace with your IP / ngrok
        const baseURL = window.location.origin;

        const qrURL = `${baseURL}/mobile-auth/${sessionId}`;

        qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${qrURL}`;

        qrStatus.innerText = "Scan QR using your phone";

        // check login
        const interval = setInterval(async ()=>{

            const check = await fetch(`/check-qr/${sessionId}`);
            const result = await check.json();

            if(result.status === "success"){

                clearInterval(interval);

                qrStatus.innerText = "Login success ✅";

                if(window.triggerWelcome) window.triggerWelcome("QR Authenticated User");
                else setTimeout(() => { window.location.href = "/"; }, 800);
            }

        },2000);

    }catch(err){
        console.error(err);
        qrStatus.innerText = "QR generation failed ❌";
        showPopup("QR error","error");
    }

});