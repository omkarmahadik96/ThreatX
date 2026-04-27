let riskHistory = [];
let trendChart;

/* Page Switching */
function openPage(e, pageId) {
    if (e) e.preventDefault();
    
    // update active tab
    document.querySelectorAll('.nav-links a').forEach(el => el.classList.remove('active'));
    if (e && e.currentTarget) e.currentTarget.classList.add('active');
    
    // update sections
    const pages = document.querySelectorAll('.page');
    pages.forEach(p => {
        p.classList.remove('active');
        p.style.display = 'none';
    });
    
    const activePage = document.getElementById(pageId);
    activePage.style.display = 'block';
    // Force reflow for animation
    void activePage.offsetWidth;
    activePage.classList.add('active');
    
    document.getElementById('page-title').innerText = e ? e.currentTarget.innerText.trim() : 'Dashboard';

    if (pageId === 'history') {
        loadHistory();
    }
}

/* Toast System */
function showToast(msg, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast-msg ${type}`;
    
    let icon = 'ph-check-circle';
    if(type === 'error') icon = 'ph-warning-circle';
    if(type === 'warning') icon = 'ph-warning';

    toast.innerHTML = `<i class="ph ${icon}" style="font-size: 24px;"></i> <div>${msg}</div>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/* Logout */
function logout(e) {
    if(e) e.preventDefault();
    
    // Trigger system shutdown animation
    const app = document.querySelector('.app-container');
    if(app) app.classList.add('system-shutdown');
    
    // Staggered departure to allow animation to play
    setTimeout(() => {
        fetch('/logout').then(() => {
            window.location.href = '/login';
        });
    }, 550);
}

/* Dashboard Scan */
function scan() {
    const url = document.getElementById('urlInput').value.trim();
    const text = document.getElementById('textInput').value.trim();

    if(!url && !text) {
        showToast("Provide a URL or text content to scan.", "warning");
        return;
    }

    const btn = document.getElementById('scanBtn');
    const loader = btn.querySelector('.loader-spinner');
    
    btn.disabled = true;
    loader.style.display = 'block';

    fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, text })
    })
    .then(res => res.json())
    .then(data => {
        btn.disabled = false;
        loader.style.display = 'none';
        
        updateDashboardUI(data);

        if(data.status.toLowerCase().includes('phishing')) showToast("Critical Threat Detected!", "error");
        else if(data.status.toLowerCase().includes('suspicious')) showToast("Suspicious Activity Found", "warning");
        else showToast("Scan Complete - Safe", "success");
    })
    .catch(err => {
        btn.disabled = false;
        loader.style.display = 'none';
        showToast("Error communicating with threat engine.", "error");
    });
}

function updateDashboardUI(data) {
    const risk = data.score || data.risk || 0;
    
    // Animate Number
    animateObjValue("riskScore", parseInt(document.getElementById("riskScore").innerText), risk, 1000);
    
    // Update Gauge (Max stroke offset is 126 for top half circle)
    const gauge = document.getElementById("gaugeProgress");
    const offset = 126 - (126 * risk / 100);
    gauge.style.strokeDashoffset = offset;

    // Set Theme Colors based on risk
    let color = "var(--success)";
    let shadow = "var(--success-glow)";
    let badgeClass = "badge-success";

    if(risk >= 40) { color = "var(--warning)"; shadow = "var(--warning-glow)"; badgeClass = "badge-warning"; }
    if(risk >= 70) { color = "var(--danger)"; shadow = "var(--danger-glow)"; badgeClass = "badge-danger"; }

    gauge.style.stroke = color;
    gauge.style.filter = `drop-shadow(0 0 10px ${shadow})`;

    const scoreTxt = document.getElementById("riskScore");
    scoreTxt.style.color = color;
    scoreTxt.style.textShadow = `0 0 20px ${shadow}`;

    // Badge
    const badge = document.getElementById("statusBadge");
    badge.className = `badge ${badgeClass}`;
    badge.innerText = data.status.toUpperCase();

    // Details Look
    document.getElementById("resIp").innerText = data.ip || "Unresolved";
    document.getElementById("resHttps").innerText = data.https ? "SECURE (HTTPS)" : "INSECURE (HTTP)";
    document.getElementById("resHttps").style.color = data.https ? "var(--success)" : "var(--danger)";

    // Reasons
    const rBox = document.getElementById("reasonsBox");
    const rList = document.getElementById("reasonsList");
    rList.innerHTML = "";
    
    if(data.reasons && data.reasons.length > 0) {
        rBox.style.display = 'block';
        data.reasons.forEach(r => {
            const li = document.createElement("li");
            li.innerText = r;
            rList.appendChild(li);
        });
    } else {
        rBox.style.display = 'none';
    }

    updateChart(risk);
}

function animateObjValue(id, start, end, duration) {
    const obj = document.getElementById(id);
    let startTs = null;
    const step = (ts) => {
        if (!startTs) startTs = ts;
        const p = Math.min((ts - startTs) / duration, 1);
        obj.innerHTML = Math.floor(p * (end - start) + start);
        if (p < 1) window.requestAnimationFrame(step);
    };
    window.requestAnimationFrame(step);
}

/* History */
function loadHistory() {
    fetch('/get_history')
    .then(res => res.json())
    .then(data => {
        const list = document.getElementById('historyList');
        const empty = document.getElementById('historyEmpty');
        list.innerHTML = "";

        if(!data || data.length === 0) {
            empty.style.display = "block";
            return;
        }
        empty.style.display = "none";

        [...data].reverse().forEach(item => {
            const risk = item.score !== undefined ? item.score : (item.risk || 0);
            let color = "var(--success)";
            if(risk >= 40) color = "var(--warning)";
            if(risk >= 70) color = "var(--danger)";

            let icon = "ph-shield-check";
            if(risk >= 40) icon = "ph-warning";
            if(risk >= 70) icon = "ph-bug";

            list.innerHTML += `
                <div class="history-item">
                    <div class="h-info">
                        <div class="h-url">${item.url || "Email Text Analysis"}</div>
                        <div class="h-meta" style="color: ${color}"><i class="ph ${icon}"></i> ${item.status.toUpperCase()}</div>
                    </div>
                    <div class="h-score" style="color: ${color}">${risk}</div>
                </div>
            `;
        });
    });
}

function clearHistory() {
    document.getElementById('deleteModal').style.display = 'flex';
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

function confirmClearHistory() {
    closeDeleteModal();
    fetch('/clear_history', { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if(data.success) {
            showToast("System history wiped successfully.", "success");
            loadHistory();
        } else {
            showToast("System wipe failed.", "error");
        }
    })
    .catch(() => {
        showToast("Error executing protocol.", "error");
    });
}

/* Chart */
function updateChart(risk) {
    riskHistory.push(risk);
    if(riskHistory.length > 15) riskHistory.shift();

    const ctx = document.getElementById("riskChart").getContext("2d");
    
    if(trendChart) trendChart.destroy();

    const grad = ctx.createLinearGradient(0, 0, 0, 300);
    grad.addColorStop(0, 'rgba(94, 106, 210, 0.4)');
    grad.addColorStop(1, 'rgba(94, 106, 210, 0.01)');

    Chart.defaults.color = "#9898a0";
    Chart.defaults.font.family = "'Inter', sans-serif";

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: riskHistory.map((_, i) => `T-${riskHistory.length-i}`),
            datasets: [{
                label: 'Risk Level',
                data: riskHistory,
                borderColor: '#5e6ad2',
                backgroundColor: grad,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#050507',
                pointBorderColor: '#5e6ad2',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: {display: false} },
            scales: {
                y: { beginAtZero: true, max: 100, grid: {color: 'rgba(255,255,255,0.05)'} },
                x: { grid: {display: false} }
            }
        }
    });
}

/* Gmail Scan Integration */
function scanGmail() {
    const btn = document.getElementById('gmailScanBtn');
    const statTxt = document.getElementById('gmailScanStatus');
    const resDiv = document.getElementById('gmailResults');

    btn.disabled = true;
    statTxt.innerHTML = "Authenticating & downloading latest emails...";
    resDiv.style.display = 'none';

    .then(async res => {
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}));
            throw new Error(errorData.status || "Scanning failed");
        }
        return res.json();
    })
    .then(data => {
        btn.disabled = false;
        
        if (data.status === "Login required") {
            statTxt.innerHTML = "Requires Google Workspace Authentication. Redirecting...";
            setTimeout(() => window.location.href = '/gmail-login', 1500);
            return;
        }

        if (data.status === "API Disabled") {
            statTxt.innerHTML = `<b style="color:var(--danger);">Gmail API Disabled.</b><br>Please enable the "Gmail API" in your Google Cloud Console for the project: <span style="color:var(--primary);">cybershild-ai</span>`;
            showToast("Gmail API not enabled in Cloud Console", "error");
            return;
        }

        statTxt.innerHTML = "Scan Complete.";
        resDiv.style.display = 'block';

        const rScore = document.getElementById('gmailRiskScore');
        const badge = document.getElementById('gmailStatusBadge');
        const rList = document.getElementById('gmailReasonsList');

        rScore.innerText = data.risk;
        
        let color = "var(--success)";
        let bdgClass = "badge-success";

        if(data.risk >= 40) { color = "var(--warning)"; bdgClass = "badge-warning"; }
        if(data.risk >= 70) { color = "var(--danger)"; bdgClass = "badge-danger"; }

        statTxt.innerHTML = `<b>Scan Complete. Connected Inbox:</b> <span style="color:var(--primary); font-family: monospace;">${data.scanned_email || "Unknown"}</span>` +
                            `<br><br><b>Inbox Scan Summary (Latest 10):</b>` +
                            `<br><span style="color:var(--success);">• ${data.safe_count || 0} Safe</span>` +
                            `&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:var(--warning);">• ${data.suspicious_count || 0} Suspicious</span>` +
                            `&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:var(--danger);">• ${data.danger_count || 0} Dangerous</span>`;

        rScore.style.color = color;
        badge.className = `badge ${bdgClass}`;
        badge.innerText = data.status.toUpperCase();

        rList.innerHTML = "";
        if(data.reasons && data.reasons.length > 0) {
            data.reasons.forEach(r => {
                const li = document.createElement("li");
                li.innerText = r;
                rList.appendChild(li);
            });
        } else {
            rList.innerHTML = "<li style='border-color: var(--success); background: rgba(48,209,88,0.05); color: var(--success);'>No threats detected in recent inbox.</li>";
        }
        
        if(data.risk >= 70) showToast("Critical Phishing emails found in inbox!", "error");
        else if(data.risk >= 40) showToast("Suspicious emails require your attention.", "warning");
        else showToast("Inbox scan complete. Looks clean.", "success");

    })
    .catch(err => {
        btn.disabled = false;
        statTxt.innerHTML = `Scanning failed: ${err.message}. Check your Vercel logs for more details.`;
        showToast("Error processing Gmail API trace.", "error");
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // Check auto_scan flag from Google OAuth
    const params = new URLSearchParams(window.location.search);
    if(params.get('auto_scan') === 'true') {
        openPage(null, 'gmail-scanner');
        setTimeout(() => scanGmail(), 800);
        window.history.replaceState({}, '', '/');
    }

    // Fetch Security Profile
    fetch('/get_user_info')
        .then(r => r.json())
        .then(data => {
            const tgt = document.getElementById('site-login-email');
            if(tgt) tgt.innerText = data.email;
            
            window.currentSessionUid = data.uid && data.uid !== 'Unknown' ? data.uid : (data.email || 'default');
            
            // Load local profile state tightly coupled to active session
            const sName = localStorage.getItem('profileName_' + window.currentSessionUid);
            const sImg = localStorage.getItem('profileImg_' + window.currentSessionUid);
            
            if(sName) {
                const pn = document.getElementById('sidebarProfileName');
                const pi = document.getElementById('profileNameInput');
                if(pn) pn.innerText = sName;
                if(pi) pi.value = sName;
            }
            if(sImg) {
                const si = document.getElementById('sidebarProfileImg');
                const sp = document.getElementById('profilePreview');
                if(si) si.src = sImg;
                if(sp) sp.src = sImg;
            }
        });

    // Theme initialization
    const themeSwitch = document.getElementById('themeSwitch');
    const label = document.getElementById('themeLabel');
    if(localStorage.getItem('theme') === 'light') {
        document.body.classList.add('light-theme');
        if(themeSwitch) themeSwitch.checked = true;
        if(label) label.innerText = "Light Mode";
    } else {
        if(themeSwitch) themeSwitch.checked = false;
        if(label) label.innerText = "Dark Mode";
    }
});

/* Theme Engine */
function toggleTheme() {
    const isChecked = document.getElementById('themeSwitch').checked;
    const label = document.getElementById('themeLabel');
    
    if(isChecked) {
        document.body.classList.add('light-theme');
        localStorage.setItem('theme', 'light');
        if(label) label.innerText = "Light Mode";
    } else {
        document.body.classList.remove('light-theme');
        localStorage.setItem('theme', 'dark');
        if(label) label.innerText = "Dark Mode";
    }
}

// Interacting to disconnect OAuth tokens
function changeGmail() {
    fetch('/disconnect-gmail', { method: 'POST' })
    .then(() => {
        window.location.href = '/gmail-login';
    });
}

// -----------------------------
// PROFILE EDITING & CROP SYSTEM
// -----------------------------
let cropper;

function openProfileModal() {
    document.getElementById('profileModal').style.display = 'block';
}

function closeProfileModal() {
    document.getElementById('profileModal').style.display = 'none';
    if(cropper) {
        cropper.destroy();
        cropper = null;
    }
    document.getElementById('cropContainer').style.display = 'none';
}

document.getElementById('profileImageInput')?.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if(file) {
        const url = URL.createObjectURL(file);
        document.getElementById('imageToCrop').src = url;
        document.getElementById('cropContainer').style.display = 'block';
        
        if(cropper) cropper.destroy();
        cropper = new Cropper(document.getElementById('imageToCrop'), {
            aspectRatio: 1,
            viewMode: 1,
            dragMode: 'move',
            autoCropArea: 0.8,
            restore: false,
            guides: true,
            center: true,
            highlight: false,
            cropBoxMovable: true,
            cropBoxResizable: true,
            toggleDragModeOnDblclick: false,
        });
    }
});

function applyCrop() {
    if(cropper) {
        const canvas = cropper.getCroppedCanvas({ width: 200, height: 200 });
        const url = canvas.toDataURL();
        document.getElementById('profilePreview').src = url;
        
        cropper.destroy();
        cropper = null;
        document.getElementById('cropContainer').style.display = 'none';
    }
}

function saveProfile() {
    const newName = document.getElementById('profileNameInput').value;
    const newSrc = document.getElementById('profilePreview').src;
    
    // Update Sidebar
    const sn = document.getElementById('sidebarProfileName');
    const si = document.getElementById('sidebarProfileImg');
    if(sn) sn.innerText = newName;
    if(si) si.src = newSrc;
    
    const uidScope = window.currentSessionUid || 'default';
    localStorage.setItem('profileName_' + uidScope, newName);
    localStorage.setItem('profileImg_' + uidScope, newSrc);
    
    closeProfileModal();
    showToast("Profile Settings Enforced", "success");
}