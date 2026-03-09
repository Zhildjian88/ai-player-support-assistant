"""
circumvention_detector.py
Detects attempts to bypass self-imposed or operator-imposed controls —
limit removal, exclusion circumvention, multi-accounting, VPN use to
re-access a blocked account.

Sources:
  - Fingerprint.com: Online Gambling Fraud Prevention (gnoming, multi-accounting)
  - UKGC enforcement cases: self-exclusion breach typologies
  - GamCare: patterns of players attempting to circumvent cooling-off periods
  - Internet Responsible Gambling Standards (NCPG, Dec 2023)

When triggered: risk_level = HIGH, flag for manual Risk team review.
Dual purpose: player welfare (circumventing their own limits) and
fraud prevention (gnoming / duplicate accounts).
"""

# ── Limit removal requests ────────────────────────────────────────────────────
# Player asking to remove or raise controls they previously set.
# Requires mandatory cool-off period before action under UKGC / MGA rules.
LIMIT_REMOVAL = [
    "remove my deposit limit", "remove my limit",
    "increase my deposit limit", "increase my limit",
    "raise my limit", "raise my deposit limit",
    "lift my limit", "lift my deposit limit",
    "cancel my deposit limit", "cancel my limit",
    "remove my loss limit", "remove my spending limit",
    "increase my loss limit", "increase my spending limit",
    "remove my session limit", "remove my time limit",
    "increase my session limit", "increase my time limit",
    "override my limit",
    # Indonesian / Malay
    "hapus batas deposit", "hapus limit saya", "batalkan batas deposit",
    "tingkatkan batas deposit", "naikkan limit saya",
    "buang had deposit", "buang limit saya", "batalkan had deposit",
    "tingkatkan had deposit", "naikkan had saya",
    "hủy giới hạn tiền gửi", "tăng giới hạn tiền gửi",
    "xóa giới hạn", "nâng giới hạn",
    # Vietnamese
    "hủy giới hạn", "tăng giới hạn", "xóa giới hạn tiền gửi",
    "nâng giới hạn tiền gửi", "bỏ giới hạn",
    # Tagalog
    "alisin ang aking limit", "palakihin ang aking limit",
    "kanselahin ang aking deposit limit", "tanggalin ang limit ko",
    # Chinese Simplified
    "取消存款限额", "删除我的限额", "提高存款限额",
    "取消限额", "我想取消我的存款限额", "提高我的限额",
    "取消我的存款限额并立即提高限额",
]

# ── Self-exclusion / cooling-off circumvention ────────────────────────────────
# Requests to undo a self-exclusion or cooling-off before its expiry.
# These must be flagged — operators are legally prohibited from acting
# immediately on such requests (mandatory 24-hour / 7-day cooling-off).
EXCLUSION_CIRCUMVENTION = [
    "remove my self exclusion", "remove my self-exclusion",
    "cancel my self exclusion", "cancel my self-exclusion",
    "end my self exclusion", "end my self-exclusion",
    "reverse my self exclusion", "undo my self exclusion",
    "lift my exclusion", "remove exclusion",
    "i want to play again", "i want to gamble again",
    "let me back in", "reopen my account",
    "remove my cooling off", "cancel my cooling off",
    "end my cooling off", "reverse my cooling off",
    "i'm ready to play again", "i changed my mind about excluding",
]

# ── Multi-accounting / gnoming ────────────────────────────────────────────────
# Signals suggesting creation of duplicate accounts to bypass controls
# or claim multiple bonuses. (Source: Fingerprint.com fraud typologies)
MULTI_ACCOUNTING = [
    "create another account", "open another account",
    "make a new account", "register a new account",
    "different email", "use a different email",
    "different name", "use a different name",
    "second account",
    "my other account", "my second account",
    "bypass the ban", "get around the ban",
    "get around the block", "bypass the block",
    "create a new profile", "new profile",
]

# ── VPN / IP circumvention ────────────────────────────────────────────────────
# Using VPN to access a geo-blocked or suspended account.
VPN_CIRCUMVENTION = [
    "use a vpn", "using a vpn", "vpn to access",
    "vpn to play", "vpn to get around",
    "change my ip", "change my location",
    "why am i blocked", "why is my account blocked",
    "why can't i access", "why am i restricted",
    "access from another country",
]

# ── Workarounds (general) ─────────────────────────────────────────────────────
GENERAL_BYPASS = [
    "bypass", "workaround", "get around my limit",
    "get around my restriction", "get around the system",
    "find a way around", "loophole",
    "still play even though excluded",
    "gamble while excluded", "play while excluded",
    "gamble with a family member's account",
    "use someone else's account",
]

CIRCUMVENTION_KEYWORDS = (
    LIMIT_REMOVAL
    + EXCLUSION_CIRCUMVENTION
    + MULTI_ACCOUNTING
    + VPN_CIRCUMVENTION
    + GENERAL_BYPASS
)

# Response differentiates between two sub-cases:
# 1. Limit/exclusion removal (welfare — explain the cooling-off requirement)
# 2. Multi-account / VPN (fraud — flag for Risk team)

WELFARE_RESPONSE = (
    "Thank you for reaching out. We take responsible gaming very seriously "
    "and have rules in place to protect players.\n\n"
    "If you set a deposit limit or cooling-off period, there is a mandatory "
    "waiting period before any changes can take effect — this is required by "
    "our licensing regulations to ensure player welfare.\n\n"
    "If you requested a self-exclusion, this cannot be reversed until the "
    "exclusion period has ended. This is a firm safeguard designed to protect you.\n\n"
    "A member of our player welfare team will review your request and contact "
    "you with more information."
)

FRAUD_RESPONSE = (
    "Thank you for contacting us. For account access and restriction queries, "
    "please verify your identity via our secure verification process.\n\n"
    "Please note that creating multiple accounts or using technical means to "
    "bypass account restrictions is a violation of our Terms of Service "
    "and may result in permanent account closure.\n\n"
    "I have flagged this query for review by our Risk and Compliance team."
)

# ── i18n responses ────────────────────────────────────────────────────────────
WELFARE_RESPONSE_I18N = {
    "en": WELFARE_RESPONSE,
    "th": (
        "ขอบคุณที่ติดต่อเรา เราให้ความสำคัญกับการเล่นพนันอย่างรับผิดชอบอย่างจริงจัง\n\n"
        "หากคุณตั้งค่าขีดจำกัดการฝากเงินหรือช่วงพักเย็น จะมีระยะเวลารอที่บังคับก่อนที่การเปลี่ยนแปลงใดๆ จะมีผล\n\n"
        "หากคุณร้องขอการยกเว้นตนเอง จะไม่สามารถยกเลิกได้จนกว่าระยะเวลาจะสิ้นสุด\n\n"
        "สมาชิกทีมสวัสดิภาพผู้เล่นของเราจะตรวจสอบคำขอของคุณและติดต่อกลับ"
    ),
    "id": (
        "Terima kasih telah menghubungi kami. Kami sangat serius dalam hal perjudian yang bertanggung jawab.\n\n"
        "Jika Anda menetapkan batas setoran atau periode pendinginan, ada periode tunggu wajib sebelum perubahan apa pun berlaku.\n\n"
        "Jika Anda meminta pengecualian diri, ini tidak dapat dibatalkan hingga periode pengecualian berakhir.\n\n"
        "Anggota tim kesejahteraan pemain kami akan meninjau permintaan Anda dan menghubungi Anda."
    ),
    "ms": (
        "Terima kasih kerana menghubungi kami. Kami mengambil perjudian bertanggungjawab dengan serius.\n\n"
        "Jika anda menetapkan had deposit atau tempoh penyejukan, terdapat tempoh menunggu wajib sebelum sebarang perubahan berkuat kuasa.\n\n"
        "Jika anda memohon pengecualian diri, ini tidak boleh dibatalkan sehingga tempoh pengecualian tamat.\n\n"
        "Ahli pasukan kebajikan pemain kami akan menyemak permintaan anda dan menghubungi anda."
    ),
    "vi": (
        "Cảm ơn bạn đã liên hệ. Chúng tôi rất coi trọng việc cờ bạc có trách nhiệm.\n\n"
        "Nếu bạn đặt giới hạn tiền gửi hoặc thời gian làm nguội, có một khoảng thời gian chờ bắt buộc trước khi bất kỳ thay đổi nào có hiệu lực.\n\n"
        "Nếu bạn yêu cầu tự loại trừ, điều này không thể đảo ngược cho đến khi thời gian loại trừ kết thúc.\n\n"
        "Thành viên nhóm phúc lợi người chơi của chúng tôi sẽ xem xét yêu cầu của bạn và liên hệ lại."
    ),
    "tl": (
        "Salamat sa pakikipag-ugnayan. Sineseryoso namin ang responsableng pagsusugal.\n\n"
        "Kung nagtakda ka ng limitasyon sa deposito o panahon ng pagpapalamig, may mandatoryong panahon ng paghihintay bago magkabisa ang anumang pagbabago.\n\n"
        "Kung humiling ka ng self-exclusion, hindi ito maaaring bawiin hanggang matapos ang panahon ng exclusion.\n\n"
        "Ang miyembro ng aming koponan ng kapakanan ng manlalaro ay susuriin ang iyong kahilingan at makikipag-ugnayan sa iyo."
    ),
}

FRAUD_RESPONSE_I18N = {
    "en": FRAUD_RESPONSE,
    "th": (
        "ขอบคุณที่ติดต่อเรา สำหรับคำถามเกี่ยวกับการเข้าถึงบัญชีและข้อจำกัด กรุณายืนยันตัวตนของคุณผ่านกระบวนการยืนยันที่ปลอดภัยของเรา\n\n"
        "โปรดทราบว่าการสร้างหลายบัญชีหรือการใช้วิธีทางเทคนิคเพื่อหลีกเลี่ยงข้อจำกัดบัญชีถือเป็นการละเมิดข้อกำหนดการให้บริการของเรา\n\n"
        "ฉันได้ทำเครื่องหมายคำถามนี้เพื่อให้ทีมความเสี่ยงและการปฏิบัติตามกฎระเบียบตรวจสอบ"
    ),
    "id": (
        "Terima kasih telah menghubungi kami. Untuk pertanyaan akses dan pembatasan akun, harap verifikasi identitas Anda melalui proses verifikasi aman kami.\n\n"
        "Harap dicatat bahwa membuat beberapa akun atau menggunakan cara teknis untuk melewati pembatasan akun melanggar Ketentuan Layanan kami.\n\n"
        "Saya telah menandai pertanyaan ini untuk ditinjau oleh tim Risiko dan Kepatuhan kami."
    ),
    "ms": (
        "Terima kasih kerana menghubungi kami. Untuk pertanyaan akses dan sekatan akaun, sila sahkan identiti anda melalui proses pengesahan selamat kami.\n\n"
        "Sila ambil perhatian bahawa mewujudkan berbilang akaun atau menggunakan cara teknikal untuk memintas sekatan akaun melanggar Syarat Perkhidmatan kami.\n\n"
        "Saya telah menandakan pertanyaan ini untuk disemak oleh pasukan Risiko dan Pematuhan kami."
    ),
    "vi": (
        "Cảm ơn bạn đã liên hệ. Để giải quyết các câu hỏi về quyền truy cập tài khoản, vui lòng xác minh danh tính của bạn qua quy trình xác minh an toàn của chúng tôi.\n\n"
        "Lưu ý rằng việc tạo nhiều tài khoản hoặc sử dụng các biện pháp kỹ thuật để vượt qua các hạn chế tài khoản là vi phạm Điều khoản Dịch vụ của chúng tôi.\n\n"
        "Tôi đã gắn cờ truy vấn này để nhóm Rủi ro và Tuân thủ của chúng tôi xem xét."
    ),
    "tl": (
        "Salamat sa pakikipag-ugnayan. Para sa mga katanungan tungkol sa access ng account, mangyaring i-verify ang iyong pagkakakilanlan sa pamamagitan ng aming secure na proseso ng pag-verify.\n\n"
        "Pakitandaan na ang paglikha ng maraming account o paggamit ng mga teknikal na paraan upang maiwasan ang mga paghihigpit sa account ay isang paglabag sa aming Mga Tuntunin ng Serbisyo.\n\n"
        "Minarkahan ko ang query na ito para sa pagsusuri ng aming koponan ng Panganib at Pagsunod."
    ),
}

_WELFARE_SIGNALS = set(LIMIT_REMOVAL + EXCLUSION_CIRCUMVENTION)
_FRAUD_SIGNALS = set(MULTI_ACCOUNTING + VPN_CIRCUMVENTION + GENERAL_BYPASS)


def check(message: str, lang: str = "en") -> dict:
    """
    Returns {"signal": bool, "subtype": str, "response": str}
    subtype: "welfare" | "fraud" | None
    """
    normalised = message.lower()
    for keyword in CIRCUMVENTION_KEYWORDS:
        if keyword in normalised:
            if keyword in _WELFARE_SIGNALS:
                return {"signal": True, "subtype": "welfare",
                        "response": WELFARE_RESPONSE_I18N.get(lang, WELFARE_RESPONSE)}
            else:
                return {"signal": True, "subtype": "fraud",
                        "response": FRAUD_RESPONSE_I18N.get(lang, FRAUD_RESPONSE)}
    return {"signal": False, "subtype": None, "response": ""}
