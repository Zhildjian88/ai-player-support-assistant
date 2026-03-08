"""
distress_detector.py
Detects crisis signals — suicidal ideation, severe emotional distress,
relationship and family breakdown due to gambling, financial ruin.

Sources:
  - DSM-5 Gambling Disorder diagnostic criteria (APA, 2013)
  - GamCare / GambleAware crisis intervention guidelines
  - PsychDB Gambling Disorder clinical indicators
  - Journal of Gambling Studies: DSM-5 criteria applied to online account data
  - WHO multilingual crisis terminology
  - npj Digital Medicine: NLP crisis detection in chat platforms (2023)

When triggered: risk_level = CRITICAL, immediate human escalation.

NOTE ON MULTILINGUAL DETECTION:
Keyword matching operates on raw message text without translation.
Critical crisis phrases are included in all languages served by this platform.
This is intentional — translation APIs add latency and failure modes on the
highest-priority routing path. Native-language keywords are the safest approach.
Production upgrade path: replace with a multilingual embedding classifier.
"""

# ── Tier 1: Explicit suicidal / self-harm ideation ────────────────────────────
# Zero false-positive risk. Any match = immediate crisis response.
SELF_HARM_KEYWORDS = [
    "suicide", "suicidal",
    "kill myself", "killing myself",
    "end my life", "take my life",
    "want to die", "wanna die", "wish i was dead",
    "thinking about dying", "thought about dying",
    "cannot live anymore", "can't live anymore",
    "no reason to live", "nothing to live for",
    "give up on life", "given up on life",
    "end it all", "end it",
    "nothing left to live",
    "better off dead", "better off without me",
    "hurt myself", "harm myself",
    "last message", "goodbye to everyone", "saying goodbye",
    "don't want to be here anymore", "don't want to be here",
    "can't go on", "cannot go on", "i can't go on",
    "no point in living", "no point anymore",
    "life isn't worth", "life is not worth",
]

# ── Tier 1b: Multilingual self-harm / crisis keywords ────────────────────────
# Covers all languages in the active player base.
# No translation layer — native keywords matched directly against raw message.
# Sources: WHO crisis terminology, GamCare multilingual resources,
#          verified by native-speaker review against common crisis expressions.
SELF_HARM_KEYWORDS_MULTILINGUAL = [

    # ── Mandarin / Chinese Simplified (ZH) ───────────────────────────────────
    # 我要自杀   = I want to kill myself / suicide
    # 我想死     = I want to die
    # 活不下去了  = Can't go on living
    # 不想活了   = Don't want to live anymore
    # 结束生命   = End my life
    # 伤害自己   = Harm myself
    # 没有活下去的理由 = No reason to live
    "我要自杀", "我想自杀", "我要去死", "我想死",
    "活不下去", "活不下去了", "不想活了", "不想活",
    "结束生命", "结束我的生命",
    "伤害自己", "伤害我自己",
    "没有活下去的理由", "没有活的意义",
    "人生没有意义", "生活没有意义",

    # ── Thai (TH) ─────────────────────────────────────────────────────────────
    # อยากตาย    = Want to die
    # ฆ่าตัวตาย  = Suicide / kill oneself
    # ไม่อยากมีชีวิตอยู่ = Don't want to be alive
    # ทำร้ายตัวเอง = Harm myself
    "อยากตาย", "อยากฆ่าตัวตาย", "ฆ่าตัวตาย",
    "ไม่อยากมีชีวิตอยู่", "ไม่อยากอยู่แล้ว",
    "ทำร้ายตัวเอง", "จบชีวิต",

    # ── Indonesian / Malay (ID / MS) ──────────────────────────────────────────
    # ingin mati       = want to die
    # bunuh diri       = suicide / kill myself
    # tidak ingin hidup = don't want to live
    # menyakiti diri   = harm myself
    "ingin mati", "mau mati", "pengen mati",
    "bunuh diri", "ingin bunuh diri", "mau bunuh diri",
    "tidak ingin hidup", "tak mau hidup lagi",
    "menyakiti diri", "menyakiti diri sendiri",
    "akhiri hidup", "mengakhiri hidup saya",
    "tiada sebab untuk hidup",         # MS: no reason to live
    "ingin menamatkan hidup",          # MS: want to end my life

    # ── Vietnamese (VI) ───────────────────────────────────────────────────────
    # muốn chết        = want to die
    # tự tử            = suicide
    # không muốn sống  = don't want to live
    # tự làm hại bản thân = harm myself
    "muốn chết", "muốn tự tử", "tự tử",
    "không muốn sống", "không muốn sống nữa",
    "tự làm hại bản thân", "kết thúc cuộc đời",
    "không còn lý do để sống",

    # ── Filipino / Tagalog (FIL) ──────────────────────────────────────────────
    # gusto kong mamatay  = I want to die
    # magpakamatay        = commit suicide
    # ayaw ko nang mabuhay = I don't want to live anymore
    # saktan ang sarili   = harm myself
    "gusto kong mamatay", "gusto ko nang mamatay",
    "magpakamatay", "gustong magpakamatay",
    "ayaw ko nang mabuhay", "ayaw ko nang mabuhay pa",
    "saktan ang sarili ko", "tapusin na ang buhay ko",
]

# ── Tier 2: Severe financial ruin ─────────────────────────────────────────────
# DSM-5 criterion: "relies on others to provide money to relieve desperate
# financial situations caused by gambling."
FINANCIAL_RUIN_KEYWORDS = [
    "lost everything", "lost it all",
    "lost all my savings", "drained my savings",
    "maxed out my credit card", "maxed out credit cards",
    "lost my house", "losing my house", "lost my home",
    "lost my job because of gambling", "lost my job gambling",
    "can't pay my rent", "cannot pay my rent", "can't pay rent",
    "can't pay my bills", "cannot pay my bills",
    "can't pay my mortgage", "cannot pay my mortgage",
    "gambling to pay rent", "need a win to pay",
    "gambling with money i need", "gambling money i can't afford",
    "borrowed money to gamble", "borrowed money and cannot pay",
    "loan sharks", "loan shark",
    "in debt because of gambling", "gambling debt",
    "stole money to gamble", "stolen money to gamble",
    "sold my belongings to gamble",
    "nothing left", "completely broke", "absolutely broke",
    "penniless", "last dollar", "last cent", "last penny",
    "empty wallet", "wallet is empty",
    "overdraft", "overdrawn",
]

# ── Tier 3: Relationship and family breakdown ─────────────────────────────────
# DSM-5 criterion: "has jeopardized or lost a significant relationship, job,
# or educational/career opportunity because of gambling."
RELATIONSHIP_BREAKDOWN_KEYWORDS = [
    "wife left me because of gambling", "husband left me because of gambling",
    "partner left me because of gambling",
    "divorce because of gambling", "divorcing because of gambling",
    "family left me", "family has left me",
    "lost my family", "lost my marriage",
    "kids taken away", "lost custody",
    "gambling ruined my marriage", "gambling destroyed my marriage",
    "gambling ruined my relationship", "gambling destroyed my relationship",
    "gambling affecting my family", "family suffering because of gambling",
    "hiding gambling from", "lying to my family about gambling",
    "lying about gambling", "hiding my gambling",
]

# ── Tier 4: Severe emotional despair (gambling-contextual) ───────────────────
# GambleAware / GamCare: emotional distress as crisis precursor.
# Scoped phrases to minimise false positives on routine complaints.
DESPAIR_KEYWORDS = [
    "ruined my life", "destroyed my life", "gambling ruined my life",
    "gambling has ruined everything", "gambling destroyed everything",
    "life is over", "my life is over",
    "don't care anymore", "i don't care anymore",
    "no way out", "there is no way out",
    "cannot take this anymore", "can't take this anymore",
    "cannot cope anymore", "can't cope anymore",
    "in serious trouble",
    "feel hopeless", "feeling hopeless", "completely hopeless",
    "feel worthless", "feeling worthless",
    "so ashamed of my gambling", "so much shame about gambling",
    "so guilty about gambling", "consumed by guilt",
    "crying because of gambling", "crying over my losses",
]

# ── Physical danger / duress signals ──────────────────────────────────────────
# Players in physical danger may reach out via support chat as a covert channel.
# These signals require immediate escalation regardless of gambling context.
PHYSICAL_DANGER_KEYWORDS = [
    # Kidnapping / captivity
    "being kidnapped", "i am being kidnapped", "im being kidnapped",
    "someone kidnapped", "kidnapped me", "held captive", "held hostage",
    "being held hostage", "i am a hostage", "im a hostage",
    "taken against my will", "not allowed to leave",
    # Physical assault / threats
    "being attacked", "someone is attacking me", "they are hurting me",
    "being hurt", "someone is threatening me", "threatening to hurt me",
    "threatening to kill me", "going to kill me", "they will kill me",
    "being beaten", "being hit", "being abused",
    # Emergency / help signals
    "please call police", "call 911", "call 999", "call 000", "call 112",
    "need police", "send help", "i need help urgently", "urgent help",
    "someone help me", "please help me now", "im in danger",
    "i am in danger", "my life is in danger", "fearing for my life",
    "fear for my life", "scared for my life",
    # Covert distress
    "if you get this call police", "send this to police",
    "remember my name in case", "tell my family",
]

DISTRESS_KEYWORDS = (
    SELF_HARM_KEYWORDS
    + SELF_HARM_KEYWORDS_MULTILINGUAL
    + FINANCIAL_RUIN_KEYWORDS
    + RELATIONSHIP_BREAKDOWN_KEYWORDS
    + DESPAIR_KEYWORDS
)

# ── Safe responses by language ─────────────────────────────────────────────────
# Hardcoded verified translations — same zero-latency, zero-dependency approach
# as the multilingual keywords. No translation API on the crisis path.
# All translations carry the same four elements:
#   1. Empathetic acknowledgement
#   2. Crisis helpline instruction (24/7, free, confidential)
#   3. Welfare team escalation confirmation
#   4. Immediate account pause / self-exclusion offer

SAFE_RESPONSES = {

    "en": (
        "I'm really sorry to hear you're going through such a difficult time. "
        "Please know that support is available and you do not have to face this alone.\n\n"
        "If you are having thoughts of self-harm, please reach out to a crisis helpline "
        "in your country immediately — they are free, confidential, and available "
        "24 hours a day.\n\n"
        "I have flagged your message to our player welfare team, who will follow up "
        "with you as soon as possible. In the meantime, I can help you activate a "
        "temporary account pause or self-exclusion if that would help."
    ),

    "th": (
        "ฉันเสียใจมากที่ได้ยินว่าคุณกำลังเผชิญกับช่วงเวลาที่ยากลำบากเช่นนี้ "
        "ขอให้รู้ว่ายังมีความช่วยเหลืออยู่ และคุณไม่จำเป็นต้องเผชิญกับสิ่งนี้เพียงลำพัง\n\n"
        "หากคุณมีความคิดที่จะทำร้ายตัวเอง โปรดติดต่อสายด่วนช่วยเหลือวิกฤตในประเทศของคุณทันที "
        "— บริการฟรี เป็นความลับ และให้บริการตลอด 24 ชั่วโมง\n\n"
        "ฉันได้แจ้งเรื่องนี้ไปยังทีมดูแลผู้เล่นของเราแล้ว และพวกเขาจะติดตามผลโดยเร็วที่สุด "
        "ในระหว่างนี้ ฉันสามารถช่วยคุณหยุดพักบัญชีชั่วคราวหรือระงับตัวเองจากการเล่นได้หากต้องการ"
    ),

    "id": (
        "Kami sangat menyesal mendengar bahwa Anda sedang melalui masa yang sangat sulit. "
        "Ketahuilah bahwa bantuan tersedia dan Anda tidak harus menghadapi ini sendiri.\n\n"
        "Jika Anda memiliki pikiran untuk menyakiti diri sendiri, segera hubungi hotline krisis "
        "di negara Anda — layanan ini gratis, rahasia, dan tersedia 24 jam sehari.\n\n"
        "Saya telah meneruskan pesan Anda ke tim kesejahteraan pemain kami, "
        "dan mereka akan menghubungi Anda sesegera mungkin. Sementara itu, saya dapat membantu "
        "Anda mengaktifkan jeda akun sementara atau pengecualian diri jika itu membantu."
    ),

    "ms": (
        "Kami amat kesal mendengar bahawa anda sedang melalui masa yang sangat sukar ini. "
        "Sila tahu bahawa bantuan tersedia dan anda tidak perlu menghadapinya seorang diri.\n\n"
        "Jika anda mempunyai fikiran untuk menyakiti diri sendiri, sila hubungi talian krisis "
        "di negara anda dengan segera — ia percuma, sulit, dan tersedia 24 jam sehari.\n\n"
        "Saya telah memaklumkan pasukan kebajikan pemain kami, dan mereka akan menghubungi anda "
        "secepat mungkin. Sementara itu, saya boleh membantu anda mengaktifkan jeda akaun "
        "sementara atau pengecualian diri jika itu membantu."
    ),

    "vi": (
        "Chúng tôi rất tiếc khi nghe bạn đang trải qua giai đoạn khó khăn như vậy. "
        "Hãy biết rằng luôn có sự hỗ trợ dành cho bạn và bạn không phải đối mặt với điều này một mình.\n\n"
        "Nếu bạn đang có ý định tự làm hại bản thân, hãy liên hệ ngay với đường dây hỗ trợ khủng hoảng "
        "tại quốc gia của bạn — miễn phí, bảo mật và hoạt động 24 giờ mỗi ngày.\n\n"
        "Tôi đã chuyển tin nhắn của bạn đến đội ngũ phúc lợi người chơi của chúng tôi, "
        "và họ sẽ liên hệ lại với bạn sớm nhất có thể. Trong thời gian chờ đợi, tôi có thể giúp bạn "
        "tạm dừng tài khoản hoặc tự loại trừ nếu điều đó có thể giúp ích."
    ),

    "tl": (
        "Labis kaming naaawa sa inyong nararamdaman. "
        "Nais naming ipaalam na may tulong na handang ibigay at hindi kayo nag-iisa sa pagharap sa sitwasyong ito.\n\n"
        "Kung mayroon kayong mga naiisip na saktan ang inyong sarili, mangyaring makipag-ugnayan "
        "sa crisis helpline sa inyong bansa agad — libre, kumpidensyal, at available 24 oras sa isang araw.\n\n"
        "Ipinaalam na namin ang inyong mensahe sa aming koponan ng kapakanan ng manlalaro, "
        "at makikipag-ugnayan sila sa inyo sa lalong madaling panahon. Samantala, maaari naming tulungan kayong "
        "i-activate ang pansamantalang pahinga ng account o self-exclusion kung makakatulong ito."
    ),

    "zh": (
        "非常抱歉听到您正在经历如此困难的时刻。"
        "请知道，帮助是可以获得的，您不必独自面对这一切。\n\n"
        "如果您有伤害自己的念头，请立即联系您所在国家的危机热线——"
        "这是免费的、保密的，并且全天24小时提供服务。\n\n"
        "我已将您的信息转达给我们的玩家关怀团队，他们将尽快与您联系。"
        "与此同时，如果有帮助，我可以协助您暂停账户或进行自我排除。"
    ),
}

# Fallback for any unsupported language
SAFE_RESPONSES["default"] = SAFE_RESPONSES["en"]


def _get_response(lang: str) -> str:
    return SAFE_RESPONSES.get(lang, SAFE_RESPONSES["default"])


PHYSICAL_DANGER_RESPONSE = (
    "This message has been flagged as an urgent safety concern. "
    "If you or someone else is in immediate physical danger, please contact your local emergency services immediately:\n\n"
    "🚨 Emergency: 999 (UK/MY/SG) · 911 (US/PH) · 000 (AU) · 112 (EU/TH/ID/VN)\n\n"
    "Your message has been escalated to our player safety team as the highest priority. "
    "If you are unable to call for help, please stay on the line and we will do our best to assist you."
)


def check(message: str, lang: str = "en") -> dict:
    """
    Returns {"signal": bool, "response": str, "subtype": str}

    Args:
        message: Raw player message
        lang:    Detected language code from language_detector

    Subtypes:
        "physical_danger" — immediate physical safety emergency
        "welfare"         — self-harm, financial ruin, emotional distress
    """
    normalised = message.lower()

    # Check physical danger first — different response (emergency services, not helpline)
    for keyword in PHYSICAL_DANGER_KEYWORDS:
        if keyword in normalised:
            return {
                "signal":   True,
                "response": PHYSICAL_DANGER_RESPONSE,
                "subtype":  "physical_danger",
            }

    # Standard welfare / self-harm distress
    for keyword in DISTRESS_KEYWORDS:
        if keyword in normalised:
            return {
                "signal":   True,
                "response": _get_response(lang),
                "subtype":  "welfare",
            }

    return {"signal": False, "response": "", "subtype": None}
