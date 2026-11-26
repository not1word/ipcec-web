#!/usr/bin/env python3
"""Tách file gốc thành: index.html (public) + admin/index.html + data.json.
Dùng: python3 build_split.py <file_goc.html> <thu_muc_ra>"""
import re, sys, os, json, subprocess

src_path, out = sys.argv[1], sys.argv[2]
S = open(src_path, encoding="utf-8").read()

def cut(s, start, end, repl=""):
    a = s.index(start); b = s.index(end, a)
    return s[:a] + repl + s[b:]

def remove_func(s, name):
    a = s.index("function %s(" % name)
    i = s.index("{", s.index(")", a)); d = 0
    for j in range(i, len(s)):
        d += (s[j] == "{") - (s[j] == "}")
        if d == 0: return s[:a] + s[j+1:]
    raise ValueError(name)

# ---- 1. data.json từ dữ liệu mặc định trong file gốc
def arr(name):
    m = re.search(r"const %s = (\[[\s\S]*?\n        \]);" % name, S)
    return json.loads(subprocess.check_output(
        ["node", "-e", "console.log(JSON.stringify(eval(process.argv[1])))", m.group(1)]))
data = {"version": 1, "banner": "", "profileUrl": "", "projects": arr("defaultProjectsData"), "news": arr("defaultNewsData")}

NEWJS = r'''
        function handleProfileDownload(e) {
            e.preventDefault();
            closeModal("profile-modal");
            if (!profileUrl) {
                showToast("Chưa cấu hình link Hồ sơ năng lực", "Vui lòng liên hệ Zalo: 0988 552 468 để nhận hồ sơ.");
                return;
            }
            window.open(profileUrl, "_blank", "noopener");
            showToast("Đang mở Hồ sơ năng lực IPCEC", "Nếu tab mới không mở, hãy cho phép cửa sổ bật lên của trình duyệt.");
        }

        function submitConsultationForm(e) {
            e.preventDefault();
            const val = id => document.getElementById(id).value.trim();
            const name = val("req-name"), phone = val("req-phone"), email = val("req-email"), note = val("req-note");
            const service = document.getElementById("req-service").value;
            const TO = "icec.vn@gmail.com", CC = "anhdt.ipcec@gmail.com", q = encodeURIComponent;
            const subject = "[icec.vn] Yêu cầu tư vấn dự án từ " + name;
            const body = "Kính gửi Ban Giám đốc IPCEC., JSC,\n\n" +
                "Họ tên người liên hệ: " + name + "\n" +
                "Số điện thoại / Zalo: " + phone + "\n" +
                "Email: " + (email || "Không cung cấp") + "\n" +
                "Lĩnh vực quan tâm: " + service + "\n" +
                "Nội dung dự án: " + (note || "Trao đổi chi tiết qua điện thoại") + "\n";
            const gmail = "https://mail.google.com/mail/?view=cm&fs=1&to=" + TO + "&cc=" + CC + "&su=" + q(subject) + "&body=" + q(body);
            const mailto = "mailto:" + TO + "?cc=" + CC + "&subject=" + q(subject) + "&body=" + q(body);
            const box = document.getElementById("consultation-result");
            box.innerHTML = `
                <div class="font-bold text-navy-900 mb-1">✓ Đã tạo thư gửi Ban Giám đốc cho ${esc(name)}</div>
                <p class="text-slate-700 mb-3">Thư đã được mở sẵn trong Gmail. Hãy bấm <strong>Gửi</strong> để hoàn tất. Nếu chưa thấy, chọn một cách bên dưới:</p>
                <div class="flex flex-wrap gap-2">
                    <a href="${gmail}" target="_blank" rel="noopener" class="px-3.5 py-2 rounded-lg bg-navy-900 text-white font-bold text-xs">Mở Gmail</a>
                    <a href="${mailto}" class="px-3.5 py-2 rounded-lg bg-slate-200 text-navy-900 font-bold text-xs">Mở ứng dụng Email</a>
                    <a href="https://zalo.me/0988552468" target="_blank" rel="noopener" class="px-3.5 py-2 rounded-lg bg-teal-600 text-white font-bold text-xs">Nhắn Zalo 0988 552 468</a>
                </div>`;
            box.classList.remove("hidden");
            window.open(gmail, "_blank", "noopener");
            e.target.reset();
        }
'''
# ---- 2. Phần chung
def common(s, data_url):
    # escape XSS khi render
    s = re.sub(r"\$\{(proj|item|p|n)\.(title|scope|capacity|location|categoryLabel|tag|date|summary)\}",
               r"${esc(\1.\2)}", s)
    s = s.replace("Hotline", "Zalo")
    s = s.replace('href="tel:0988552468"', 'href="https://zalo.me/0988552468" target="_blank" rel="noopener"')
    s = remove_func(s, "handleProfileDownload"); s = remove_func(s, "submitConsultationForm")
    s = s.replace('window.addEventListener("DOMContentLoaded"', NEWJS + '\n        window.addEventListener("DOMContentLoaded"', 1)
    loader = '''const DATA_URL = "%s";
        let bannerData = "";
        let profileUrl = "";
        function esc(v) { return String(v == null ? "" : v).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
        async function loadAppData() {
            let d = null;
            try {
                const r = await fetch(DATA_URL + "?v=" + Date.now(), { cache: "no-store" });
                if (r.ok) d = await r.json();
            } catch (e) {}
            /*DRAFT*/
            projectsData = (d && d.projects) || JSON.parse(JSON.stringify(defaultProjectsData));
            newsData = (d && d.news) || JSON.parse(JSON.stringify(defaultNewsData));
            bannerData = (d && d.banner) || "";
            profileUrl = (d && d.profileUrl) || "";
            const pin = document.getElementById("cms-profile-url"); if (pin) pin.value = profileUrl;
            if (bannerData) document.getElementById("hero-banner-img").src = bannerData;
            renderProjects(); renderNews();
        }
        ''' % data_url
    return cut(s, "function loadAppData()", "function navigateTo", loader)

# ---- 3. PUBLIC
P = common(S, "data.json")
P = cut(P, "<!-- ==================== ADMIN ACTIVE", "<!-- ==================== TOP CORPORATE")
P = cut(P, "<!-- ==================== MODAL: ADMIN LOGIN", "<!-- ==================== TOAST MESSAGE")
P = re.sub(r'<button[^>]*id="header-admin-btn"[^>]*>.*?</button>\s*', "", P, flags=re.S)
P = re.sub(r'<button onclick="handleAdminButtonClick\(\)" class="underline[^>]*>.*?</button>', "", P, flags=re.S)
P = cut(P, "/* Secure Production Admin CMS Functions */", "let toastTimer")
P = re.sub(r'window\.addEventListener\("DOMContentLoaded"[\s\S]*?\n        \}\);', 'window.addEventListener("DOMContentLoaded", loadAppData);', P)
P = re.sub(r'\n        const defaultAdminPassword = "[^"]*";', "", P)
P = P.replace("let isAdminLoggedIn = false;", "const isAdminLoggedIn = false;")
P = re.sub(r"\n\s*const STORAGE_KEYS = \{[\s\S]*?\};", "", P)
P = re.sub(r'\$\{isAdminLoggedIn \? `[\s\S]*?` : ""\}', "", P)
P = P.replace("const isAdminLoggedIn = false;\n", "")
assert not re.search(r"ipcec2026|localStorage|sessionStorage|Admin|admin-|deleteProject|deleteNews", P)

# ---- 4. ADMIN
A = common(S, "../data.json")
A = A.replace('<meta charset="UTF-8">', '<meta charset="UTF-8">\n    <meta name="robots" content="noindex, nofollow">', 1)
A = A.replace("<title>IPCEC", "<title>ADMIN | IPCEC", 1)
A = A.replace('<link rel="canonical" href="https://icec.vn/">', "")
A = re.sub(r'\n        const defaultAdminPassword = "[^"]*";', "", A)
A = A.replace("let isAdminLoggedIn = false;", "let isAdminLoggedIn = true; // xác thực do server (Basic Auth / Cloudflare Access) đảm nhiệm")
A = cut(A, "<!-- ==================== MODAL: ADMIN LOGIN", "<!-- ==================== MODAL: ADMIN CMS DASHBOARD")
A = re.sub(r'<button onclick="openAdminCMS\(\'security\'\)"[^>]*>.*?</button>\s*', "", A)
A = re.sub(r'<button onclick="logoutAdmin\(\)"[^>]*>.*?</button>\s*', "", A)
A = re.sub(r'<button id="cms-tab-btn-security"[^>]*>.*?</button>\s*', "", A)
A = cut(A, "<!-- Pane 4: Security & Password -->", "<!-- Pane 5: Production Export -->")
A = cut(A, "<!-- Pane 5: Production Export -->", "<!-- ==================== TOAST MESSAGE", '''<!-- Pane: Export data.json -->
            <div id="cms-pane-export" class="hidden">
                <div class="p-5 rounded-xl border border-teal-300 bg-teal-50 max-w-xl">
                    <h4 class="font-bold text-navy-900 text-base mb-1.5">Xuất data.json để đưa lên icec.vn</h4>
                    <p class="text-xs sm:text-sm text-slate-700 mb-4">Tải <strong>data.json</strong> rồi upload đè lên file cùng tên ở thư mục gốc website. Không cần sửa <strong>index.html</strong>.</p>
                    <div class="flex flex-wrap gap-2">
                        <button onclick="exportData()" class="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs sm:text-sm font-bold shadow">Tải xuống data.json</button>
                        <button onclick="discardDraft()" class="px-4 py-2.5 rounded-xl border border-slate-300 text-xs sm:text-sm font-bold">Bỏ bản nháp, tải lại từ server</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    ''')
A = A.replace('<h4 class="font-bold text-navy-900 text-sm">Thay đổi ảnh bìa Trang chủ (Hero Banner)</h4>', '<div class="pb-3 border-b border-slate-200 space-y-2"><label class="block text-xs font-bold text-navy-900">Link Hồ sơ năng lực (Google Drive, chia sẻ "Bất kỳ ai có đường liên kết")</label><div class="flex gap-2"><input type="text" id="cms-profile-url" class="flex-1 px-3 py-2 rounded-lg border border-slate-300 text-xs" placeholder="https://drive.google.com/file/d/..."><button onclick="saveProfileUrl()" class="px-4 py-2 rounded-lg bg-navy-900 text-white text-xs font-bold">Lưu</button></div></div><h4 class="font-bold text-navy-900 text-sm">Thay đổi ảnh bìa Trang chủ (Hero Banner)</h4>')
A = A.replace("3. Đổi ảnh Hero Banner", "3. Banner & Hồ sơ")
A = A.replace("5. Xuất bản Hosting (.html)", "4. Xuất data.json").replace("Xuất bản index.html", "Xuất data.json")
A = A.replace('onclick="exportPackagedHTML()"', 'onclick="exportData()"')
A = A.replace('["projects", "news", "banner", "security", "export"]', '["projects", "news", "banner", "export"]')
for f in ["getActivePassword", "submitAdminLogin", "logoutAdmin", "changeAdminPassword", "resetDefaultPassword", "exportData" if False else "exportPackagedHTML", "handleAdminButtonClick"]:
    if "function %s(" % f in A: A = remove_func(A, f)
A = re.sub(r"\n\s*const STORAGE_KEYS = \{[\s\S]*?\};", "", A)
A = A.replace("try { localStorage.setItem(STORAGE_KEYS.BANNER, ev.target.result); } catch (e) {}", "bannerData = ev.target.result; saveDraft();")
A = A.replace("try { localStorage.setItem(STORAGE_KEYS.BANNER, url); } catch (e) {}", "bannerData = url; saveDraft();")
A = A.replace("/*DRAFT*/", '''try {
                const dr = JSON.parse(localStorage.getItem(DRAFT_KEY) || "null");
                if (dr) { d = dr; showToast("Đang dùng bản nháp chưa xuất", "Bấm Xuất data.json để đăng lên website."); }
            } catch (e) {}''')
A = A.replace("const DATA_URL", '''const DRAFT_KEY = "ipcec_admin_draft_v2";
        function saveDraft() {
            try { localStorage.setItem(DRAFT_KEY, JSON.stringify({ banner: bannerData, profileUrl: profileUrl, projects: projectsData, news: newsData })); } catch (e) {}
        }
        function saveProfileUrl() {
            profileUrl = document.getElementById("cms-profile-url").value.trim();
            saveDraft(); showToast("Đã lưu link Hồ sơ năng lực", "Nhớ xuất data.json để đăng lên website.");
        }
        function saveProjects() { saveDraft(); }
        function saveNews() { saveDraft(); }
        function handleAdminButtonClick() { openAdminCMS("projects"); }
        function discardDraft() { try { localStorage.removeItem(DRAFT_KEY); } catch (e) {} location.reload(); }
        function exportData() {
            const payload = { version: 1, updated: new Date().toISOString(), banner: bannerData, profileUrl: profileUrl, projects: projectsData, news: newsData };
            const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
            const a = document.createElement("a"); a.href = url; a.download = "data.json";
            document.body.appendChild(a); a.click(); document.body.removeChild(a);
            setTimeout(() => URL.revokeObjectURL(url), 1000);
            showToast("Đã xuất data.json", "Upload file này lên thư mục gốc icec.vn (đè file cũ).");
        }
        const DATA_URL''', 1)
A = re.sub(r'window\.addEventListener\("DOMContentLoaded"[\s\S]*?\n        \}\);', 'window.addEventListener("DOMContentLoaded", () => loadAppData().then(updateAdminState));', A)
assert "ipcec2026" not in A

os.makedirs(out + "/admin", exist_ok=True)
open(out + "/index.html", "w", encoding="utf-8").write(P)
open(out + "/admin/index.html", "w", encoding="utf-8").write(A)
json.dump(data, open(out + "/data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("OK")
