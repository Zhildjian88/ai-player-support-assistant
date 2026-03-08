"""
streamlit_player.py
Player-facing support chat interface for SiDOBet Casino.

What this shows:
    - Player login / profile selection screen with language selector
    - Account summary (tier, status, balance, KYC) — labels in selected language
    - Responsible Gaming banner (compliance requirement)
    - Quick action buttons — labels and responses in selected language
    - Clean chat interface with multilingual support

What this hides (visible in streamlit_app.py ops console):
    - Route taken, confidence, risk flags
    - Audit log, escalation queue internals
    - Cost dashboard, LLM call rate
    - Detector names (distress_detector, rg_detector, etc.)

Architecture:
    Same FastAPI /chat endpoint as the ops console.
    The routing engine, safety layer, and LLM fallback are identical.
    Only the presentation layer changes.
    Language selection sets the Accept-Language header on /chat so the
    backend responds in the player's preferred language.

Run:
    streamlit run ui/streamlit_player.py
    (API must be running on http://localhost:8000)
"""

import os
import sys
import requests
import streamlit as st
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.router_bridge import chat as bridge_chat

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SiDOBet Support",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Design system ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
.stApp { background: #0d0f14; color: #e8eaf0; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; padding-bottom: 1rem; }

.player-card {
    background: linear-gradient(135deg, #1a1d27 0%, #12151e 100%);
    border: 1px solid #2a2d3a; border-radius: 16px;
    padding: 20px; margin-bottom: 12px;
}
.tier-diamond  { background: linear-gradient(135deg, #a8edea, #fed6e3); color: #111; }
.tier-platinum { background: linear-gradient(135deg, #c0c0c0, #e8e8e8); color: #111; }
.tier-gold     { background: linear-gradient(135deg, #f6d365, #fda085); color: #111; }
.tier-standard { background: #2a2d3a; color: #888; }
.tier-badge {
    display: inline-block; padding: 3px 12px; border-radius: 20px;
    font-size: 0.72em; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
}
.rg-banner {
    background: linear-gradient(90deg, #1a2744 0%, #162035 100%);
    border-left: 3px solid #3b82f6; border-radius: 8px;
    padding: 10px 16px; margin-bottom: 16px;
    font-size: 0.82em; color: #93c5fd;
}
.user-bubble {
    background: linear-gradient(135deg, #6366f1, #4f46e5); color: white;
    border-radius: 18px 18px 4px 18px; padding: 12px 16px;
    margin: 4px 0; max-width: 80%; margin-left: auto;
    font-size: 0.9em; line-height: 1.5;
}
.bot-bubble {
    background: #1a1d27; border: 1px solid #2a2d3a; color: #e2e8f0;
    border-radius: 18px 18px 18px 4px; padding: 12px 16px;
    margin: 4px 0; max-width: 80%; font-size: 0.9em; line-height: 1.6;
}
.stButton > button {
    background: #1a1d27 !important; border: 1px solid #2a2d3a !important;
    color: #c8cde0 !important; border-radius: 10px !important;
    font-family: 'Sora', sans-serif !important; font-size: 0.82em !important;
    padding: 8px 12px !important; transition: all 0.2s !important;
}
.stButton > button:hover {
    border-color: #6366f1 !important; color: #a5b4fc !important;
    background: #1e2133 !important;
}
.metric-card {
    background: #1a1d27; border: 1px solid #2a2d3a;
    border-radius: 12px; padding: 14px 16px; text-align: center;
}
.metric-value { font-size: 1.3em; font-weight: 700; color: #e2e8f0; font-family: 'JetBrains Mono', monospace; }
.metric-label { font-size: 0.72em; color: #64748b; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.06em; }
.support-alert {
    background: linear-gradient(135deg, #1e1a2e, #1a1d27);
    border-left: 3px solid #f59e0b; border-radius: 8px;
    padding: 12px 16px; font-size: 0.85em; color: #fcd34d; margin-top: 8px;
}
.lang-btn-active {
    background: linear-gradient(135deg,#6366f1,#4f46e5) !important;
    border-color: #6366f1 !important; color: white !important; font-weight: 700 !important;
}
/* Dark chat input box */
.stChatInput textarea, .stChatInput input, [data-testid="stChatInput"] textarea {
    background: #1a1d27 !important;
    color: #e2e8f0 !important;
    border: 1px solid #2a2d3a !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"] {
    background: #0d0f14 !important;
    border-top: 1px solid #1e2130 !important;
}
/* Dark selectbox on login screen */
.stSelectbox > div > div {
    background: #1a1d27 !important;
    color: #c8cde0 !important;
    border: 1px solid #2a2d3a !important;
    border-radius: 10px !important;
}
/* Language flag buttons — dark background, fixed height */
button[data-testid="baseButton-secondary"] {
    background: #1e2235 !important;
    border: 1px solid #2a2d3a !important;
    color: #94a3b8 !important;
    min-height: 64px !important;
    line-height: 1.4 !important;
}
button[data-testid="baseButton-secondary"]:hover {
    border-color: #6366f1 !important;
    color: #a5b4fc !important;
    background: #1a1d27 !important;
}
/* Active lang button — purple (applied via .lang-btn-active class) */
.lang-btn-active button, .lang-btn-active button:focus {
    background: linear-gradient(135deg,#6366f1,#4f46e5) !important;
    border-color: #6366f1 !important;
    color: white !important;
    font-weight: 700 !important;
}
/* Enter Support Chat — primary button always purple */
button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg,#6366f1,#4f46e5) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 0.95em !important;
    padding: 12px !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Player data ───────────────────────────────────────────────────────────────
PLAYERS = {
    "U1001": { "name":"Budi Santoso",    "flag":"🇮🇩", "country":"Indonesia",   "tier":"standard", "status":"active",     "kyc":"verified", "lang":"id", "balance":"IDR 2,840,000",   "pending_withdrawal":"IDR 1,500,000 (under review)", "member_since":"Jun 2024", "rg_flag":False },
    "U1002": { "name":"Somchai Prayoon", "flag":"🇹🇭", "country":"Thailand",    "tier":"gold",     "status":"active",     "kyc":"verified", "lang":"th", "balance":"THB 18,500",      "pending_withdrawal":None,                            "member_since":"Nov 2023", "rg_flag":False },
    "U1003": { "name":"James Wilson",    "flag":"🇦🇺", "country":"Australia",   "tier":"standard", "status":"restricted", "kyc":"pending",  "lang":"en", "balance":"AUD 240",         "pending_withdrawal":"AUD 80 (blocked — KYC required)","member_since":"Feb 2026", "rg_flag":False },
    "U1005": { "name":"Nguyen Van An",   "flag":"🇻🇳", "country":"Vietnam",     "tier":"platinum", "status":"active",     "kyc":"verified", "lang":"vi", "balance":"VND 48,200,000",  "pending_withdrawal":None,                            "member_since":"Aug 2022", "rg_flag":False },
    "U1009": { "name":"Tran Thi Bich",   "flag":"🇻🇳", "country":"Vietnam",     "tier":"diamond",  "status":"active",     "kyc":"verified", "lang":"vi", "balance":"VND 182,500,000", "pending_withdrawal":None,                            "member_since":"May 2021", "rg_flag":False },
    "U1010": { "name":"Juan dela Cruz",  "flag":"🇵🇭", "country":"Philippines", "tier":"gold",     "status":"active",     "kyc":"verified", "lang":"tl", "balance":"PHP 24,600",      "pending_withdrawal":None,                            "member_since":"Jul 2023", "rg_flag":False },
    "U1006": { "name":"Siriporn Kamon",  "flag":"🇹🇭", "country":"Thailand",    "tier":"standard", "status":"active",     "kyc":"verified", "lang":"th", "balance":"THB 3,200",       "pending_withdrawal":None,                            "member_since":"Jan 2025", "rg_flag":True  },
}

LANGUAGES = [
    {"code":"en", "label":"English",          "flag":"🇬🇧"},
    {"code":"th", "label":"ภาษาไทย",          "flag":"🇹🇭"},
    {"code":"id", "label":"Bahasa Indonesia", "flag":"🇮🇩"},
    {"code":"vi", "label":"Tiếng Việt",       "flag":"🇻🇳"},
    {"code":"tl", "label":"Filipino",         "flag":"🇵🇭"},
    {"code":"zh", "label":"中文",             "flag":"🇨🇳"},
]

# ── i18n strings ──────────────────────────────────────────────────────────────
UI = {
    "en": {
        "select_account":  "Select your account to continue",
        "select_language": "Language",
        "enter_chat":      "Enter Support Chat →",
        "footer":          "🔒 Secure · 🌐 Multilingual · 🛡️ Responsible Gaming",
        "live_chat":       "Live Chat",
        "switch_btn":      "← Switch",
        "rg_banner":       "Responsible Gaming",
        "rg_active":       "⚠️ RG tools active on your account",
        "rg_default":      "Set deposit limits | Track your spend | Stay in control",
        "rg_manage":       "Manage →",
        "acct_summary":    "Account Summary",
        "pending_with":    "⏳ Pending Withdrawal",
        "quick_actions":   "Quick Actions",
        "welcome_title":   lambda n: f"Welcome back, {n} 👋",
        "welcome_body":    "I'm your SiDOBet Support assistant. I can help you with withdrawals, account queries, game rules, promotions, and responsible gaming tools.",
        "welcome_sub":     "Type your question below or use the Quick Actions panel.",
        "placeholder":     "Type your message here… (any language supported)",
        "send":            "Send",
        "escalated":       "⚡ A support agent has been notified and will follow up with you shortly.",
        "balance_lbl":     "Balance", "status_lbl": "Status", "kyc_lbl": "KYC", "tier_lbl": "Tier",
        "status_val":      {"active":"Active","restricted":"Restricted","suspended":"Suspended","self_excluded":"Self-Excluded"},
        "tier_val":        {"diamond":"Diamond","platinum":"Platinum","gold":"Gold","standard":"Standard"},
        "kyc_val":         {"verified":"Verified","pending":"Pending","failed":"Failed"},
        "qa_labels":       ["💳 Check Balance","⏳ Withdrawal Status","🎁 Active Promotions","🔐 KYC Status","🎮 Game Rules & T&C","🛡️ Responsible Gaming"],
        "qa_msgs":         ["What is my current account balance and recent transactions?","What is the status of my pending withdrawal?","What promotions and bonuses are available for me right now?","What is my KYC verification status?","Where can I find the rules for the games and the terms and conditions?","I need help with responsible gaming tools and deposit limits."],
    },
    "th": {
        "select_account":  "เลือกบัญชีของคุณเพื่อดำเนินการต่อ",
        "select_language": "ภาษา",
        "enter_chat":      "เข้าสู่แชทสนับสนุน →",
        "footer":          "🔒 ปลอดภัย · 🌐 หลายภาษา · 🛡️ การเล่นที่รับผิดชอบ",
        "live_chat":       "แชทสด",
        "switch_btn":      "← เปลี่ยน",
        "rg_banner":       "การเล่นเกมอย่างรับผิดชอบ",
        "rg_active":       "⚠️ เครื่องมือ RG เปิดใช้งานในบัญชีของคุณ",
        "rg_default":      "ตั้งวงเงินฝาก | ติดตามการใช้จ่าย | ควบคุมตัวเอง",
        "rg_manage":       "จัดการ →",
        "acct_summary":    "สรุปบัญชี",
        "pending_with":    "⏳ การถอนเงินที่รอดำเนินการ",
        "quick_actions":   "การดำเนินการด่วน",
        "welcome_title":   lambda n: f"ยินดีต้อนรับกลับมา, {n} 👋",
        "welcome_body":    "ฉันคือผู้ช่วยสนับสนุน SiDOBet ฉันสามารถช่วยคุณเกี่ยวกับการถอนเงิน การสอบถามบัญชี กฎของเกม โปรโมชัน และเครื่องมือการเล่นเกมอย่างรับผิดชอบ",
        "welcome_sub":     "พิมพ์คำถามของคุณด้านล่าง หรือใช้แผงการดำเนินการด่วน",
        "placeholder":     "พิมพ์ข้อความของคุณที่นี่…",
        "send":            "ส่ง",
        "escalated":       "⚡ ได้แจ้งเจ้าหน้าที่สนับสนุนแล้ว และจะติดตามผลกับคุณในเร็วๆ นี้",
        "balance_lbl":     "ยอดเงิน", "status_lbl": "สถานะ", "kyc_lbl": "KYC", "tier_lbl": "ระดับ",
        "status_val":      {"active":"ใช้งานอยู่","restricted":"ถูกจำกัด","suspended":"ถูกระงับ","self_excluded":"ยกเว้นตนเอง"},
        "tier_val":        {"diamond":"ไดมอนด์","platinum":"แพลทินัม","gold":"ทอง","standard":"มาตรฐาน"},
        "kyc_val":         {"verified":"ยืนยันแล้ว","pending":"รอดำเนินการ","failed":"ไม่ผ่าน"},
        "qa_labels":       ["💳 ตรวจสอบยอดเงิน","⏳ สถานะการถอนเงิน","🎁 โปรโมชันที่ใช้งานอยู่","🔐 สถานะ KYC","🎮 กฎเกม & ข้อตกลง","🛡️ การเล่นเกมอย่างรับผิดชอบ"],
        "qa_msgs":         ["What is my current account balance and recent transactions?","What is the status of my pending withdrawal?","What promotions and bonuses are available for me right now?","What is my KYC verification status?","Where can I find the rules for the games and the terms and conditions?","I need help with responsible gaming tools and deposit limits."],
    },
    "id": {
        "select_account":  "Pilih akun Anda untuk melanjutkan",
        "select_language": "Bahasa",
        "enter_chat":      "Masuk ke Obrolan Dukungan →",
        "footer":          "🔒 Aman · 🌐 Multibahasa · 🛡️ Permainan Bertanggung Jawab",
        "live_chat":       "Live Chat",
        "switch_btn":      "← Ganti",
        "rg_banner":       "Permainan Bertanggung Jawab",
        "rg_active":       "⚠️ Alat RG aktif di akun Anda",
        "rg_default":      "Atur batas setoran | Lacak pengeluaran | Tetap terkendali",
        "rg_manage":       "Kelola →",
        "acct_summary":    "Ringkasan Akun",
        "pending_with":    "⏳ Penarikan Tertunda",
        "quick_actions":   "Tindakan Cepat",
        "welcome_title":   lambda n: f"Selamat datang kembali, {n} 👋",
        "welcome_body":    "Saya adalah asisten Dukungan SiDOBet. Saya dapat membantu Anda dengan penarikan, pertanyaan akun, aturan permainan, promosi, dan alat permainan bertanggung jawab.",
        "welcome_sub":     "Ketik pertanyaan Anda di bawah atau gunakan panel Tindakan Cepat.",
        "placeholder":     "Ketik pesan Anda di sini…",
        "send":            "Kirim",
        "escalated":       "⚡ Agen dukungan telah diberitahu dan akan menindaklanjuti Anda segera.",
        "balance_lbl":     "Saldo", "status_lbl": "Status", "kyc_lbl": "KYC", "tier_lbl": "Tingkat",
        "status_val":      {"active":"Aktif","restricted":"Dibatasi","suspended":"Ditangguhkan","self_excluded":"Pengecualian Diri"},
        "tier_val":        {"diamond":"Diamond","platinum":"Platinum","gold":"Emas","standard":"Standar"},
        "kyc_val":         {"verified":"Terverifikasi","pending":"Tertunda","failed":"Gagal"},
        "qa_labels":       ["💳 Cek Saldo","⏳ Status Penarikan","🎁 Promosi Aktif","🔐 Status KYC","🎮 Aturan Game & S&K","🛡️ Permainan Bertanggung Jawab"],
        "qa_msgs":         ["What is my current account balance and recent transactions?","What is the status of my pending withdrawal?","What promotions and bonuses are available for me right now?","What is my KYC verification status?","Where can I find the rules for the games and the terms and conditions?","I need help with responsible gaming tools and deposit limits."],
    },
    "vi": {
        "select_account":  "Chọn tài khoản của bạn để tiếp tục",
        "select_language": "Ngôn ngữ",
        "enter_chat":      "Vào Chat Hỗ Trợ →",
        "footer":          "🔒 Bảo mật · 🌐 Đa ngôn ngữ · 🛡️ Chơi game có trách nhiệm",
        "live_chat":       "Chat Trực Tiếp",
        "switch_btn":      "← Chuyển",
        "rg_banner":       "Chơi Game Có Trách Nhiệm",
        "rg_active":       "⚠️ Công cụ RG đang hoạt động trên tài khoản của bạn",
        "rg_default":      "Đặt giới hạn nạp | Theo dõi chi tiêu | Kiểm soát bản thân",
        "rg_manage":       "Quản lý →",
        "acct_summary":    "Tóm Tắt Tài Khoản",
        "pending_with":    "⏳ Rút Tiền Đang Chờ",
        "quick_actions":   "Thao Tác Nhanh",
        "welcome_title":   lambda n: f"Chào mừng trở lại, {n} 👋",
        "welcome_body":    "Tôi là trợ lý Hỗ trợ SiDOBet của bạn. Tôi có thể giúp bạn về rút tiền, truy vấn tài khoản, quy tắc trò chơi, khuyến mãi và các công cụ chơi game có trách nhiệm.",
        "welcome_sub":     "Nhập câu hỏi của bạn bên dưới hoặc sử dụng bảng Thao Tác Nhanh.",
        "placeholder":     "Nhập tin nhắn của bạn tại đây…",
        "send":            "Gửi",
        "escalated":       "⚡ Nhân viên hỗ trợ đã được thông báo và sẽ liên hệ với bạn sớm.",
        "balance_lbl":     "Số dư", "status_lbl": "Trạng thái", "kyc_lbl": "KYC", "tier_lbl": "Hạng",
        "status_val":      {"active":"Hoạt động","restricted":"Bị hạn chế","suspended":"Bị tạm ngừng","self_excluded":"Tự loại trừ"},
        "tier_val":        {"diamond":"Kim Cương","platinum":"Bạch Kim","gold":"Vàng","standard":"Tiêu Chuẩn"},
        "kyc_val":         {"verified":"Đã xác minh","pending":"Đang chờ","failed":"Thất bại"},
        "qa_labels":       ["💳 Kiểm Tra Số Dư","⏳ Trạng Thái Rút Tiền","🎁 Khuyến Mãi Đang Hoạt Động","🔐 Trạng Thái KYC","🎮 Luật Chơi & Điều Khoản","🛡️ Chơi Game Có Trách Nhiệm"],
        "qa_msgs":         ["What is my current account balance and recent transactions?","What is the status of my pending withdrawal?","What promotions and bonuses are available for me right now?","What is my KYC verification status?","Where can I find the rules for the games and the terms and conditions?","I need help with responsible gaming tools and deposit limits."],
    },
    "tl": {
        "select_account":  "Piliin ang iyong account para magpatuloy",
        "select_language": "Wika",
        "enter_chat":      "Pumasok sa Support Chat →",
        "footer":          "🔒 Ligtas · 🌐 Maraming Wika · 🛡️ Responsableng Paglalaro",
        "live_chat":       "Live Chat",
        "switch_btn":      "← Palitan",
        "rg_banner":       "Responsableng Paglalaro",
        "rg_active":       "⚠️ Aktibo ang mga RG tool sa iyong account",
        "rg_default":      "Magtakda ng limitasyon | Subaybayan ang gastos | Manatiling kontrolado",
        "rg_manage":       "Pamahalaan →",
        "acct_summary":    "Buod ng Account",
        "pending_with":    "⏳ Nakabinbing Withdrawal",
        "quick_actions":   "Mabilis na Aksyon",
        "welcome_title":   lambda n: f"Maligayang pagbabalik, {n} 👋",
        "welcome_body":    "Ako ang iyong SiDOBet Support assistant. Maaari kitang tulungan sa mga withdrawal, katanungan sa account, patakaran ng laro, promosyon, at mga tool para sa responsableng paglalaro.",
        "welcome_sub":     "I-type ang iyong tanong sa ibaba o gamitin ang Quick Actions panel.",
        "placeholder":     "I-type ang iyong mensahe dito…",
        "send":            "Ipadala",
        "escalated":       "⚡ Naabisuhan na ang isang ahente ng suporta at makikipag-ugnayan sa iyo sa lalong madaling panahon.",
        "balance_lbl":     "Balanse", "status_lbl": "Katayuan", "kyc_lbl": "KYC", "tier_lbl": "Antas",
        "status_val":      {"active":"Aktibo","restricted":"Limitado","suspended":"Suspendido","self_excluded":"Self-Excluded"},
        "tier_val":        {"diamond":"Diamond","platinum":"Platinum","gold":"Ginto","standard":"Pamantayan"},
        "kyc_val":         {"verified":"Napatunayan","pending":"Nakabinbin","failed":"Nabigo"},
        "qa_labels":       ["💳 Tingnan ang Balanse","⏳ Katayuan ng Withdrawal","🎁 Mga Aktibong Promosyon","🔐 Katayuan ng KYC","🎮 Mga Patakaran ng Laro & T&C","🛡️ Responsableng Paglalaro"],
        "qa_msgs":         ["What is my current account balance and recent transactions?","What is the status of my pending withdrawal?","What promotions and bonuses are available for me right now?","What is my KYC verification status?","Where can I find the rules for the games and the terms and conditions?","I need help with responsible gaming tools and deposit limits."],
    },
    "zh": {
        "select_account":  "请选择您的账户以继续",
        "select_language": "语言",
        "enter_chat":      "进入客服聊天 →",
        "footer":          "🔒 安全 · 🌐 多语言 · 🛡️ 负责任博彩",
        "live_chat":       "在线客服",
        "switch_btn":      "← 切换",
        "rg_banner":       "负责任博彩",
        "rg_active":       "⚠️ 您的账户已启用 RG 工具",
        "rg_default":      "设置存款限额 | 跟踪消费 | 保持自控",
        "rg_manage":       "管理 →",
        "acct_summary":    "账户摘要",
        "pending_with":    "⏳ 待处理提款",
        "quick_actions":   "快速操作",
        "welcome_title":   lambda n: f"欢迎回来，{n} 👋",
        "welcome_body":    "我是您的 SiDOBet 客服助手。我可以帮您处理提款、账户查询、游戏规则、促销活动以及负责任博彩工具。",
        "welcome_sub":     "请在下方输入您的问题，或使用快速操作面板。",
        "placeholder":     "在此输入您的消息…",
        "send":            "发送",
        "escalated":       "⚡ 已通知客服专员，他们将尽快跟进您的情况。",
        "balance_lbl":     "余额", "status_lbl": "状态", "kyc_lbl": "KYC", "tier_lbl": "等级",
        "status_val":      {"active":"正常","restricted":"受限","suspended":"已暂停","self_excluded":"自我排除"},
        "tier_val":        {"diamond":"钻石","platinum":"铂金","gold":"黄金","standard":"标准"},
        "kyc_val":         {"verified":"已验证","pending":"待审核","failed":"未通过"},
        "qa_labels":       ["💳 查询余额","⏳ 提款状态","🎁 当前优惠活动","🔐 KYC 状态","🎮 游戏规则 & 条款","🛡️ 负责任博彩"],
        "qa_msgs":         ["What is my current account balance and recent transactions?","What is the status of my pending withdrawal?","What promotions and bonuses are available for me right now?","What is my KYC verification status?","Where can I find the rules for the games and the terms and conditions?","I need help with responsible gaming tools and deposit limits."],
    },
}

TIER_ICONS   = {"diamond":"💎","platinum":"🥈","gold":"🥇","standard":"🎰"}
STATUS_COLOR = {"active":"#4ade80","restricted":"#fb923c","suspended":"#f87171","self_excluded":"#94a3b8"}

# ── Session state ─────────────────────────────────────────────────────────────
if "logged_in"  not in st.session_state: st.session_state.logged_in  = False
if "player_id"  not in st.session_state: st.session_state.player_id  = "U1003"
if "ui_lang"    not in st.session_state: st.session_state.ui_lang    = PLAYERS["U1003"]["lang"]
if "messages"   not in st.session_state: st.session_state.messages   = []
if "session_id" not in st.session_state: st.session_state.session_id = None
if "prefill"        not in st.session_state: st.session_state.prefill         = ""
if "pending_action" not in st.session_state: st.session_state.pending_action  = ""


# ── Login screen ──────────────────────────────────────────────────────────────
def render_login():
    t = UI.get(st.session_state.ui_lang, UI["en"])

    sorted_players = sorted(PLAYERS.items(), key=lambda x: (x[1]["country"], x[1]["name"]))
    player_options = {f"{p['flag']} {p['country']} — {p['name']} ({pid})": pid for pid, p in sorted_players}
    labels = list(player_options.keys())
    default_label = next(k for k, v in player_options.items() if v == st.session_state.player_id)

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
    [data-testid="stAppViewContainer"] { background: #0d0f14 !important; }
    [data-testid="stHeader"] { background: transparent !important; }
    .stApp { background: #0d0f14; }
    /* Strip all widget box chrome inside login column */
    section[data-testid="stMain"] .block-container { padding-top: 0.5rem !important; }
    div[data-testid="stVerticalBlock"] > div[data-testid="element-container"],
    div[data-testid="stVerticalBlock"] > div.stMarkdown { background: transparent !important; border: none !important; box-shadow: none !important; }
    div[data-testid="stVerticalBlock"] { gap: 4px !important; }
    /* Dark selectbox */
    .stSelectbox > div > div { background: #1e2235 !important; color: #c8cde0 !important; border: 1px solid #2a2d3a !important; border-radius: 10px !important; font-size: 0.88em !important; }
    /* Language buttons — base style */
    div[data-testid="column"] button { background: #1a1d27 !important; border: 1px solid #2a2d3a !important; color: #94a3b8 !important; min-height: 72px !important; border-radius: 10px !important; }
    div[data-testid="column"] button:hover { border-color: #6366f1 !important; color: #a5b4fc !important; }
    /* Active language — purple (set via .lang-on wrapper) */
    .lang-on button { background: linear-gradient(135deg,#6366f1,#4f46e5) !important; border-color: #6366f1 !important; color: white !important; font-weight: 700 !important; }
    /* Enter button */
    .enter-btn button { background: linear-gradient(135deg,#6366f1,#4f46e5) !important; border: none !important; color: white !important; font-weight: 600 !important; font-size: 0.95em !important; border-radius: 12px !important; padding: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

    _, col_c, _ = st.columns([1, 2, 1])
    with col_c:

        # Logo
        st.markdown("""
        <div style="text-align:center; padding: 6px 0 12px 0;">
            <div style="font-size:3em; margin-bottom:10px;">🎰</div>
            <div style="font-size:1.6em; font-weight:800; color:white; letter-spacing:-0.02em;">SiDOBet</div>
            <div style="color:#64748b; font-size:0.9em; margin-top:4px;">Player Support Centre</div>
        </div>
        """, unsafe_allow_html=True)

        # Account selector label
        st.markdown(f"<div style='color:#94a3b8; font-size:0.8em; margin-bottom:6px;'>{t['select_account']}</div>",
                    unsafe_allow_html=True)

        # Selectbox
        selected = st.selectbox("", labels, index=labels.index(default_label), label_visibility="collapsed")
        pid = player_options[selected]

        if pid != st.session_state.player_id:
            st.session_state.player_id = pid
            st.session_state.ui_lang   = PLAYERS[pid]["lang"]
            st.rerun()

        p  = PLAYERS[pid]
        t  = UI.get(st.session_state.ui_lang, UI["en"])
        ti = TIER_ICONS.get(p["tier"], "🎰")
        sc = STATUS_COLOR.get(p["status"], "#94a3b8")
        sv = t["status_val"].get(p["status"], p["status"])
        kv = t["kyc_val"].get(p["kyc"], p["kyc"])
        tier_bg = (
            "linear-gradient(135deg,#a8edea,#fed6e3)" if p["tier"] == "diamond" else
            "linear-gradient(135deg,#c0c0c0,#e8e8e8)" if p["tier"] == "platinum" else
            "linear-gradient(135deg,#f6d365,#fda085)" if p["tier"] == "gold" else "#2a2d3a"
        )
        tier_color = "#111" if p["tier"] != "standard" else "#8e97a4"

        # Player card — fully dynamic, self-contained
        st.markdown(f"""
        <div style="background:#1a1d27; border:1px solid #2a2d3a; border-radius:16px; padding:24px; margin-top:12px;">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <div style="font-size:1.1em; font-weight:700; color:#e2e8f0;">{p["flag"]} {p["name"]}</div>
                    <div style="color:#64748b; font-size:0.8em; margin-top:3px;">{p["country"]} · Since {p["member_since"]}</div>
                </div>
                <span style="background:{tier_bg}; color:{tier_color}; padding:4px 12px; border-radius:8px;
                             font-size:0.7em; font-weight:700; text-transform:uppercase; white-space:nowrap;">
                    {ti} {p["tier"].upper()}
                </span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:20px; text-align:center;">
                <div>
                    <div style="color:{sc}; font-weight:700;">{sv}</div>
                    <div style="font-size:0.7em; color:#475569; margin-top:2px;">{t["status_lbl"]}</div>
                </div>
                <div>
                    <div style="color:#e2e8f0; font-weight:700;">{kv}</div>
                    <div style="font-size:0.7em; color:#475569; margin-top:2px;">{t["kyc_lbl"]}</div>
                </div>
                <div>
                    <div style="color:#e2e8f0; font-weight:700;">{p["balance"]}</div>
                    <div style="font-size:0.7em; color:#475569; margin-top:2px;">{t["balance_lbl"]}</div>
                </div>
            </div>
        </div>
        <div style="margin-top:20px; color:#64748b; font-size:0.75em; font-weight:600; letter-spacing:0.08em;">LANGUAGE</div>
        """, unsafe_allow_html=True)

        # Language grid — two rows of 3
        for row in [LANGUAGES[:3], LANGUAGES[3:]]:
            lang_cols = st.columns(3)
            for i, lang in enumerate(row):
                with lang_cols[i]:
                    cls = "lang-on" if st.session_state.ui_lang == lang["code"] else ""
                    st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
                    if st.button(lang["flag"] + "\n" + lang["label"], key="L_" + lang["code"], use_container_width=True):
                        st.session_state.ui_lang = lang["code"]
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

        # Enter button
        st.markdown('<div class="enter-btn" style="margin-top:16px;">', unsafe_allow_html=True)
        if st.button(t["enter_chat"], use_container_width=True, key="enter_btn"):
            st.session_state.logged_in  = True
            st.session_state.messages   = []
            st.session_state.session_id = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            f'<div style="text-align:center; color:#475569; font-size:0.72em; margin-top:20px;">{t["footer"]}</div>',
            unsafe_allow_html=True
        )


# ── Chat screen ───────────────────────────────────────────────────────────────
def render_chat():
    pid = st.session_state.player_id
    p   = PLAYERS[pid]
    t   = UI.get(st.session_state.ui_lang, UI["en"])
    tier_icon    = TIER_ICONS.get(p["tier"], "🎰")
    status_color = STATUS_COLOR.get(p["status"], "#94a3b8")

    # ── Top bar ───────────────────────────────────────────────────────────────
    col_logo, col_info, col_lang, col_logout = st.columns([1, 3, 2, 1])
    with col_logo:
        st.markdown("<div style='font-size:1.4em; font-weight:700; color:#e2e8f0; padding-top:4px;'>🎰 SiDOBet</div>", unsafe_allow_html=True)
    with col_info:
        st.markdown(
            f"<div style='font-size:0.82em; color:#64748b; padding-top:8px;'>"
            f"● <span style='color:#4ade80;'>{t['live_chat']}</span> &nbsp;|&nbsp; "
            f"{p['flag']} {p['name']} &nbsp;|&nbsp; "
            f"<span class='tier-badge tier-{p['tier']}' style='font-size:0.85em;'>{tier_icon} {p['tier'].upper()}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
    with col_lang:
        # Compact flag switcher
        flag_cols = st.columns(len(LANGUAGES))
        for i, lang in enumerate(LANGUAGES):
            with flag_cols[i]:
                label = f"{'→' if st.session_state.ui_lang == lang['code'] else ''}{lang['flag']}"
                if st.button(lang["flag"], key=f"chat_lang_{lang['code']}", help=lang["label"]):
                    st.session_state.ui_lang = lang["code"]
                    st.rerun()
    with col_logout:
        if st.button(t["switch_btn"], use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.messages  = []
            st.rerun()

    # ── RG Banner ─────────────────────────────────────────────────────────────
    rg_msg = t["rg_active"] if p.get("rg_flag") else t["rg_default"]
    rg_col, manage_col = st.columns([5, 1])
    with rg_col:
        st.markdown(f"""
    <div class="rg-banner">
        🛡️ <b>{t['rg_banner']}</b> &nbsp;|&nbsp; {rg_msg}
    </div>
        """, unsafe_allow_html=True)
    with manage_col:
        if st.button(t["rg_manage"], key="rg_manage_btn", use_container_width=True):
            st.session_state.pending_action = "action:rg"
            st.rerun()

    # ── Two-column layout ─────────────────────────────────────────────────────
    col_panel, col_chat = st.columns([1, 2.4])

    with col_panel:
        status_val = t["status_val"].get(p["status"], p["status"])
        kyc_val    = t["kyc_val"].get(p["kyc"], p["kyc"])
        tier_val   = t["tier_val"].get(p["tier"], p["tier"])

        st.markdown(f"""
        <div class="player-card">
            <div style="font-size:0.72em; color:#475569; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:10px;">{t['acct_summary']}</div>
            <div style="font-size:1.05em; font-weight:600; color:#e2e8f0;">{p['flag']} {p['name']}</div>
            <div style="font-size:0.78em; color:#64748b; margin-top:2px;">{pid}</div>
            <div style="margin-top:14px; display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                <div class="metric-card">
                    <div class="metric-value" style="font-size:0.9em;">{p['balance']}</div>
                    <div class="metric-label">{t['balance_lbl']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="font-size:0.9em; color:{status_color};">{status_val}</div>
                    <div class="metric-label">{t['status_lbl']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="font-size:0.9em;">{kyc_val}</div>
                    <div class="metric-label">{t['kyc_lbl']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="font-size:0.85em;">{tier_icon} {tier_val}</div>
                    <div class="metric-label">{t['tier_lbl']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if p.get("pending_withdrawal"):
            st.markdown(f"""
            <div style="background:#1a1d27; border:1px solid #2a2d3a; border-left:3px solid #fb923c;
                        border-radius:10px; padding:12px 14px; margin-bottom:12px; font-size:0.82em;">
                <div style="color:#fb923c; font-weight:600; margin-bottom:4px;">{t['pending_with']}</div>
                <div style="color:#94a3b8;">{p['pending_withdrawal']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(
            f"<div style='font-size:0.75em; color:#475569; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;'>{t['quick_actions']}</div>",
            unsafe_allow_html=True
        )
        for label, msg in zip(t["qa_labels"], t["qa_msgs"]):
            if st.button(label, use_container_width=True, key=f"qa_{label}"):
                st.session_state.prefill = msg
                st.rerun()

    with col_chat:
        if not st.session_state.messages:
            first_name = p["name"].split()[0]
            lang_list  = " · ".join(l["label"] for l in LANGUAGES)
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1e2235,#151825);
                        border:1px solid #2a2d3a; border-radius:16px; padding:20px 24px; margin-bottom:16px;">
                <div style="font-size:1.05em; font-weight:600; color:#e2e8f0; margin-bottom:6px;">
                    {t['welcome_title'](first_name)}
                </div>
                <div style="font-size:0.85em; color:#64748b; line-height:1.6;">
                    {t['welcome_body']}<br><br>{t['welcome_sub']}
                </div>
                <div style="margin-top:14px; font-size:0.78em; color:#475569;">
                    🌐 {lang_list}
                </div>
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="display:flex; justify-content:flex-end; margin:8px 0;">
                    <div class="user-bubble">{msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display:flex; gap:10px; margin:8px 0; align-items:flex-start;">
                    <div style="width:32px; height:32px; border-radius:50%;
                                background:linear-gradient(135deg,#6366f1,#4f46e5);
                                display:flex; align-items:center; justify-content:center;
                                font-size:16px; flex-shrink:0;">🤖</div>
                    <div class="bot-bubble">{msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)
                if msg.get("escalated"):
                    st.markdown(f"""
                    <div class="support-alert">{t['escalated']}</div>
                    """, unsafe_allow_html=True)

        # Consume pending_action (from quick action buttons or Manage →) first
        pending     = st.session_state.pop("pending_action", "") or st.session_state.pop("prefill", "")
        user_input  = st.chat_input(t["placeholder"], key="player_chat_input")
        if pending and not user_input:
            user_input = pending

        if user_input:
            # Show translated label in chat bubble, not raw action token
            _ACTION_LABELS = {
                "action:balance":    t["qa_labels"][0],
                "action:withdrawal": t["qa_labels"][1],
                "action:promotions": t["qa_labels"][2],
                "action:kyc":        t["qa_labels"][3],
                "action:rules":      t["qa_labels"][4],
                "action:rg":         t["qa_labels"][5],
            }
            display_input = _ACTION_LABELS.get(user_input.strip(), user_input)
            st.session_state.messages.append({"role":"user","content":display_input})
            try:
                data = bridge_chat(
                    message    = user_input,
                    user_id    = pid,
                    session_id = st.session_state.session_id,
                    lang       = st.session_state.ui_lang,
                )
                st.session_state.session_id = data.get("session_id")
                st.session_state.messages.append({
                    "role":      "assistant",
                    "content":   data["response"],
                    "escalated": data.get("escalated", False),
                })
            except requests.exceptions.ConnectionError:
                st.session_state.messages.append({
                    "role":      "assistant",
                    "content":   "⚠️ Our support service is temporarily unavailable. Please try again in a moment or contact us via email.",
                    "escalated": False,
                })
            except Exception as e:
                import traceback
                err_detail = traceback.format_exc()
                print(f"[streamlit_player] bridge error: {err_detail}")
                st.session_state.messages.append({
                    "role":      "assistant",
                    "content":   f"⚠️ Error: {type(e).__name__}: {e}",
                    "escalated": False,
                })
            st.rerun()


# ── Router ────────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    render_login()
else:
    render_chat()
