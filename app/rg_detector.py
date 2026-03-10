"""
rg_detector.py
Detects responsible gaming signals — problem gambling, compulsion,
loss of control, harm to finances or relationships, tool requests.

Sources:
  - DSM-5 Gambling Disorder criteria: tolerance, withdrawal, loss of control,
    preoccupation, chasing, escapism, deception, bailout, jeopardised relationships
  - GamCare / GambleAware intervention taxonomy
  - Internet Responsible Gambling Standards (NCPG, Dec 2023)
  - Journal of Gambling Studies: online account-based harm indicators

When triggered: risk_level = HIGH, escalate with RG tool offer.
"""

# ── Loss of control & compulsion ──────────────────────────────────────────────
# DSM-5: "persistent unsuccessful efforts to control, cut back, or stop"
LOSS_OF_CONTROL = [
    "cannot stop gambling", "can't stop gambling", "cant stop gambling",
    "unable to stop gambling", "tried to stop gambling",
    "tried to quit gambling", "keep going back to gambling",
    "gambling again even though", "relapsed gambling",
    "hooked on gambling", "hooked on betting",
    "obsessed with gambling", "obsessed with betting",
    "one more go", "just one more bet", "just one more spin",
    "last bet", "last spin", "last hand",
    "can't resist gambling", "cannot resist gambling",
    "urge to gamble", "urge to bet", "craving to gamble",
    "can't help myself gambling",
    # Indonesian / Malay
    "tidak boleh berhenti berjudi", "tidak bisa berhenti berjudi",
    "tidak dapat berhenti berjudi", "sudah rugi banyak",
    "tidak boleh berhenti", "kecanduan judi", "kecanduan berjudi",
    "ketagihan berjudi", "tidak boleh kawal perjudian",
    "tidak dapat berhenti", "susah berhenti berjudi",
    # Vietnamese
    "không thể dừng cờ bạc", "không dừng được", "nghiện cờ bạc",
    "không kiểm soát được việc cờ bạc", "cứ tiếp tục đánh bạc",
    # Tagalog
    "hindi ako makatigil sa pagsusugal", "hindi ko mapigilan ang pagsusugal",
    "sugal na sugal ako", "adik sa sugal",
    # Thai
    "หยุดเล่นการพนันไม่ได้", "เลิกพนันไม่ได้", "หยุดไม่ได้",
    "ติดการพนัน", "เล่นการพนันมากเกินไป", "ควบคุมการพนันไม่ได้",
    "อยากเลิกแต่ทำไม่ได้", "เล่นไม่หยุด",
    # Chinese Simplified
    "无法停止赌博", "不能停止赌博", "停不下来",
    "每天都在赌博", "沉迷赌博", "赌博成瘾",
    "戒不掉赌博", "无法控制赌博", "忍不住赌博",
]

# ── Preoccupation & time distortion ──────────────────────────────────────────
# DSM-5: "preoccupied with gambling" / academic: prolonged sessions
PREOCCUPATION = [
    "gambling all night", "betting all night", "been gambling for hours",
    "gambled all day", "gambling everyday", "gambling every day",
    "gambling all the time", "can't stop thinking about gambling",
    "lost track of time gambling", "lost track of time",
    "only thing i think about", "all i think about is gambling",
    "gambling instead of sleeping", "gambling instead of working",
    "missed work because of gambling", "late because of gambling",
]

# ── Chasing losses ────────────────────────────────────────────────────────────
# DSM-5: "often returns another day to get even" / chasing criterion
CHASING = [
    "chasing losses", "chasing my losses", "chase my loss", "chase my loses",
    "chase losses", "chase the loss",
    "trying to win back", "win back what i lost",
    "get my money back", "get back my losses",
    "need to win back", "have to win it back",
    "keep depositing to recover", "depositing more to chase",
    "doubling up to recover", "increasing bets to recover",
    "win back my money", "recover my losses", "recover my money",
]

# ── Gambling as income delusion ───────────────────────────────────────────────
# Signals player may believe gambling is a reliable income source — HIGH risk
INCOME_DELUSION = [
    "bet to make money", "betting to make money", "gamble to make money",
    "gambling to make money", "gambling for income", "betting for income",
    "make money from gambling", "make money from betting",
    "make money from casino", "make a living from gambling",
    "make a living from betting", "live off gambling",
    "teach me how to make", "teach me to win",
    "how to make million", "make millions gambling",
    "get rich from gambling", "get rich from betting",
    "make profit from gambling", "guaranteed win", "guaranteed profit",
    "sure win", "sure bet", "can\'t lose", "cannot lose",
]

# ── Gambling as escape ────────────────────────────────────────────────────────
# DSM-5: "gambles as a way of escaping problems or relieving dysphoric mood"
ESCAPISM = [
    "gamble to forget", "gambling to forget",
    "gamble to escape", "gambling to escape",
    "gamble when stressed", "gambling when stressed",
    "gamble when depressed", "gambling when depressed",
    "gambling to cope", "gamble to cope",
    "gambling helps me feel better", "only feel good when gambling",
    "gambling is the only thing that helps",
    "use gambling to deal with",
]

# ── Financial harm signals ────────────────────────────────────────────────────
# DSM-5: relying on others for financial bailout; spending beyond means
FINANCIAL_HARM = [
    "spending too much on gambling", "spend too much on gambling",
    "spending more than i should", "spent more than i can afford",
    "gambling money i need", "gambling my rent money",
    "gambling my bill money", "gambling my savings",
    "losing too much", "lost too much money gambling",
    "keep losing money", "losing more and more",
    "gambling with money i don't have",
    "asked family for money to gamble", "borrowed money for gambling",
    "need money to gamble", "need a deposit to keep going",
    "begging for bonus", "please give me a bonus to continue",
]

# ── Irritability & withdrawal ─────────────────────────────────────────────────
# DSM-5: "restless or irritable when attempting to cut down or stop"
# Academic: aggressive CS communication as withdrawal signal
WITHDRAWAL = [
    "irritable when i don't gamble", "restless when i can't gamble",
    "anxious when i can't bet", "moody when i can't gamble",
    "need to gamble to feel normal", "feel terrible when not gambling",
]

# ── Deception & secrecy ───────────────────────────────────────────────────────
# DSM-5: "has lied to conceal the extent of involvement with gambling"
DECEPTION = [
    "hiding my gambling", "hiding gambling from my family",
    "lying about gambling", "lying to my partner about gambling",
    "lying to my wife about gambling", "lying to my husband about gambling",
    "secret gambling account", "gambling in secret",
    "deleted my betting history", "hiding transactions",
]

# ── Explicit tool requests ────────────────────────────────────────────────────
# Player-initiated requests for RG tools — highest intent signal
TOOL_REQUESTS = [
    "self exclude", "self-exclude", "self exclusion", "self-exclusion",
    "close my account", "block my account", "freeze my account",
    "delete my account", "deactivate my account",
    "set a deposit limit", "set my deposit limit", "set deposit limit",
    "set a spending limit", "set a loss limit", "set a wager limit",
    "set a session limit", "set a time limit",
    "remove my deposit limit", "increase my deposit limit", "change my deposit limit",
    "cooling off", "cooling-off period", "take a break from gambling",
    "pause my account", "temporary block",
    "need help with gambling", "help me stop gambling", "help me stop",
    "gamstop", "gamban", "gambling blocker",
    "self-assessment", "gambling quiz", "am i a problem gambler",
    "responsible gaming tools", "safer gambling tools",
    # Indonesian / Malay
    "bantu saya berhenti berjudi", "tolong bantu saya berhenti",
    "ingin berhenti berjudi", "mau berhenti berjudi",
    "tetapkan batas deposit", "batasi deposit saya",
    "kecualikan diri saya", "pengecualian diri",
    "blokir akaun saya", "tangguhkan akaun saya",
    "bantuan masalah judi", "tolong saya berhenti berjudi",
    # Vietnamese
    "giúp tôi dừng cờ bạc", "tôi muốn dừng cờ bạc",
    "tự loại trừ", "đặt giới hạn tiền gửi",
    "khóa tài khoản tạm thời", "cần giúp đỡ về cờ bạc",
    # Tagalog
    "tulungan mo akong tumigil sa pagsusugal",
    "gusto kong huminto sa pagsusugal",
    "i-block ang aking account", "mag-self exclude",
    # Chinese Simplified
    "帮我停止赌博", "我想停止赌博", "设置存款限额",
    "暂停我的账户", "自我排除", "需要赌博帮助",
    "冻结我的账户", "关闭我的账户",
]

# ── Relationship & social harm ────────────────────────────────────────────────
SOCIAL_HARM = [
    "gambling affecting my family", "gambling affecting my relationship",
    "gambling affecting my marriage", "gambling affecting my work",
    "affecting my family", "affecting my relationship",
    "partner upset about my gambling", "wife upset about gambling",
    "husband upset about gambling", "argument about gambling",
    "family intervention about gambling",
    "addicted to gambling", "gambling addiction", "gambling problem",
    "problem gambler", "compulsive gambler", "compulsive gambling",
    # Indonesian / Malay
    "keluarga akan meninggalkan saya", "keluarga mau meninggalkan",
    "istri mau cerai karena judi", "masalah perjudian",
    "keluarga saya akan tinggalkan", "keluarga nak tinggalkan saya",
    "keluarga akan pergi", "rumahtangga terjejas kerana judi",
    # Vietnamese
    "gia đình sắp rời bỏ tôi", "vợ sắp bỏ tôi vì cờ bạc",
    "cờ bạc ảnh hưởng gia đình", "nghiện cờ bạc",
    # Tagalog
    "sugal ang dahilan ng away namin", "iniwan ako ng pamilya dahil sa sugal",
    "apektado ang pamilya ko sa sugal",
    # Chinese Simplified
    "家人要离开我了", "家人快要离开我", "因为赌博家人要离开",
    "赌博影响家庭", "赌博成瘾", "有赌博问题",
    "因赌博妻子要离婚", "赌博毁了我的家庭",
]

# ── General / catch-all ───────────────────────────────────────────────────────
GENERAL = [
    "cannot control", "can't control my gambling", "out of control",
    "losing control", "lost control of gambling",
    "spend too much", "spending too much",
    "cannot control my spending",
    # Thai general
    "เล่นมากเกินไป", "แพ้มากเกินไป", "ใช้เงินมากเกินไป",
    "ควบคุมตัวเองไม่ได้", "เล่นการพนันทุกวัน", "ติดพนัน",
    "เสียเงินมากเกินไป", "หมดเงินเพราะพนัน",
]

RG_KEYWORDS = (
    LOSS_OF_CONTROL
    + PREOCCUPATION
    + CHASING
    + INCOME_DELUSION
    + ESCAPISM
    + FINANCIAL_HARM
    + WITHDRAWAL
    + DECEPTION
    + TOOL_REQUESTS
    + SOCIAL_HARM
    + GENERAL
)

SAFE_RESPONSE = (
    "Thank you for reaching out. Recognising when gambling may be affecting you "
    "is an important step.\n\n"
    "We offer a range of responsible gaming tools including:\n"
    "• Deposit limits (daily, weekly, monthly)\n"
    "• Session time limits\n"
    "• Cooling-off periods (24 hours to 30 days)\n"
    "• Self-exclusion (6 months to permanent)\n\n"
    "You can access these in the Responsible Gaming section of your Account Settings, "
    "or our support team can help you set them up right now via live chat.\n\n"
    "If you would like to speak with someone, free confidential support is available "
    "through gambling helplines in your country."
)


# Informational questions about RG tools — should go to FAQ, not trigger RG response
# These are "how does it work" questions, not "I need help" signals
RG_INFO_EXCLUSIONS = [
    "how do i set a deposit limit", "how do i set a spending limit",
    "how do i set a loss limit", "how do i set a session limit",
    "how do i set a time limit", "how do i set a wager limit",
    "how to set a deposit limit", "how to set a spending limit",
    "how do i change my deposit limit", "how do i change my limit",
    "how do i access responsible gaming", "where can i find responsible gaming",
    "what is a deposit limit", "what are deposit limits",
    "what is responsible gaming", "what is a cooling off",
    "what is a session limit", "what is a time limit",
    "tell me about responsible gaming", "explain responsible gaming",
]

def check(message: str) -> dict:
    normalised = message.lower()
    # Informational "how do I..." questions belong in FAQ, not RG escalation
    if any(excl in normalised for excl in RG_INFO_EXCLUSIONS):
        return {"signal": False, "response": ""}
    for keyword in RG_KEYWORDS:
        if keyword in normalised:
            return {"signal": True, "response": SAFE_RESPONSE}
    return {"signal": False, "response": ""}

SAFE_RESPONSE_I18N = {
    "id": (
        "Terima kasih telah menghubungi kami. Menyadari bahwa perjudian mungkin memengaruhi Anda "
        "adalah langkah yang penting.\n\n"
        "Kami menawarkan berbagai alat permainan bertanggung jawab, termasuk:\n"
        "• Batas setoran (harian, mingguan, bulanan)\n"
        "• Batas waktu sesi\n"
        "• Periode pendinginan (24 jam hingga 30 hari)\n"
        "• Pengecualian diri (6 bulan hingga permanen)\n\n"
        "Anda dapat mengaksesnya di bagian Permainan Bertanggung Jawab di Pengaturan Akun Anda, "
        "atau tim dukungan kami dapat membantu Anda mengaturnya sekarang melalui live chat.\n\n"
        "Jika Anda ingin berbicara dengan seseorang, dukungan rahasia gratis tersedia "
        "melalui hotline perjudian di negara Anda."
    ),
    "th": (
        "ขอบคุณที่ติดต่อเรา การรู้ว่าการพนันอาจส่งผลกระทบต่อคุณเป็นก้าวสำคัญ\n\n"
        "เราเสนอเครื่องมือการเล่นอย่างรับผิดชอบ ได้แก่:\n"
        "• วงเงินฝาก (รายวัน รายสัปดาห์ รายเดือน)\n"
        "• จำกัดเวลาเล่น\n"
        "• ช่วงพักการเล่น (24 ชั่วโมง ถึง 30 วัน)\n"
        "• การยกเว้นตนเอง (6 เดือน ถึงถาวร)\n\n"
        "คุณสามารถเข้าถึงได้ในส่วนการเล่นอย่างรับผิดชอบในการตั้งค่าบัญชีของคุณ "
        "หรือทีมสนับสนุนของเราสามารถช่วยตั้งค่าผ่านแชทสดได้เลย\n\n"
        "หากต้องการพูดคุยกับผู้เชี่ยวชาญ สายด่วนให้คำปรึกษาด้านการพนันในประเทศของคุณพร้อมให้บริการฟรี"
    ),
    "vi": (
        "Cảm ơn bạn đã liên hệ. Nhận ra rằng cờ bạc có thể ảnh hưởng đến bạn là một bước quan trọng.\n\n"
        "Chúng tôi cung cấp các công cụ chơi có trách nhiệm bao gồm:\n"
        "• Giới hạn nạp tiền (hàng ngày, hàng tuần, hàng tháng)\n"
        "• Giới hạn thời gian chơi\n"
        "• Thời gian nghỉ (24 giờ đến 30 ngày)\n"
        "• Tự loại trừ (6 tháng đến vĩnh viễn)\n\n"
        "Bạn có thể truy cập trong phần Chơi Có Trách Nhiệm trong Cài đặt Tài khoản, "
        "hoặc đội hỗ trợ có thể giúp bạn thiết lập ngay qua live chat.\n\n"
        "Nếu muốn nói chuyện với ai đó, hỗ trợ bảo mật miễn phí có sẵn qua đường dây hỗ trợ tại quốc gia bạn."
    ),
    "tl": (
        "Salamat sa pakikipag-ugnayan. Ang pagkilala na maaaring maapektuhan ka ng pagsusugal ay isang mahalagang hakbang.\n\n"
        "Nag-aalok kami ng iba't ibang kasangkapan para sa responsableng paglalaro kabilang ang:\n"
        "• Limitasyon sa deposito (araw-araw, lingguhan, buwanan)\n"
        "• Limitasyon sa oras ng sesyon\n"
        "• Panahon ng pahinga (24 oras hanggang 30 araw)\n"
        "• Self-exclusion (6 buwan hanggang permanente)\n\n"
        "Maaari mong ma-access ang mga ito sa seksyon ng Responsableng Paglalaro sa iyong Mga Setting ng Account, "
        "o ang aming koponan ng suporta ay makakatulong sa iyo ngayon sa pamamagitan ng live chat.\n\n"
        "Kung nais kang makipag-usap sa isang tao, ang libreng suporta ay available sa pamamagitan ng mga helpline sa iyong bansa."
    ),
    "zh": (
        "感谢您的联系。意识到赌博可能正在影响您是重要的一步。\n\n"
        "我们提供一系列负责任博彩工具，包括：\n"
        "• 存款限额（每日、每周、每月）\n"
        "• 会话时间限制\n"
        "• 冷静期（24小时至30天）\n"
        "• 自我排除（6个月至永久）\n\n"
        "您可以在账户设置的负责任博彩部分访问这些工具，"
        "或者我们的支持团队现在可以通过在线聊天帮助您设置。\n\n"
        "如果您想与某人交谈，可通过您所在国家的赌博帮助热线获得免费保密支持。"
    ),
}


def check_with_lang(message: str, lang: str = "en") -> dict:
    normalised = message.lower()
    for keyword in RG_KEYWORDS:
        if keyword in normalised:
            response = SAFE_RESPONSE_I18N.get(lang, SAFE_RESPONSE)
            return {"signal": True, "response": response}
    return {"signal": False, "response": ""}
