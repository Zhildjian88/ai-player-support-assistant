"""
payment_service.py
Looks up real payment/withdrawal/deposit status from SQLite.
Never invents status values — all data comes from the database.
Responses are localised to the player's detected language.
"""

PAYMENT_TRIGGERS = [
    "withdrawal", "withdraw", "payout", "cashout", "cash out",
    "my deposit", "check deposit", "deposit status", "transaction",
    "payment status", "transfer", "pending payment", "my money",
    "where is my", "when will my",
    # Indonesian / Malay
    "penarikan", "tarik tunai", "pengeluaran", "status pembayaran",
    "wang saya", "duit saya", "di mana wang",
    # Vietnamese
    "rút tiền", "nạp tiền", "trạng thái thanh toán", "tiền của tôi",
    # Tagalog
    "withdrawal ko", "mag-withdraw", "deposito ko", "pera ko",
    "kailan darating", "status ng withdrawal",
    # Thai
    "ถอนเงิน", "ฝากเงิน", "สถานะการชำระเงิน", "เงินของฉัน",
]

# These indicate a question ABOUT deposits/payments, not a status lookup
PAYMENT_EXCLUSIONS = [
    "deposit declined", "deposit failed", "deposit not working",
    "why was my deposit", "why is my deposit", "deposit rejected",
    "payment declined", "payment failed", "payment method",
    "change my payment", "add payment", "remove payment",
    "travelling", "travel", "different country", "vpn",
    "play from", "access from",
]

# ── i18n status message templates ─────────────────────────────────────────────
STATUS_TEMPLATES = {
    "en": {
        "PENDING":    "Your {ptype} of {ccy} {amount} via {method} is currently pending. {notes}",
        "PROCESSING": "Your {ptype} of {ccy} {amount} via {method} is being processed. {notes}",
        "COMPLETED":  "Your {ptype} of {ccy} {amount} via {method} has been completed successfully.",
        "REJECTED":   "Your {ptype} of {ccy} {amount} via {method} was not processed. Reason: {notes}",
        "BLOCKED":    "Your {ptype} of {ccy} {amount} via {method} has been blocked. Reason: {notes}",
        "FAILED":     "Your {ptype} of {ccy} {amount} via {method} failed. {notes} Please try again or contact support.",
        "UNKNOWN":    "Your {ptype} of {ccy} {amount} has status: {status}. Please contact support for details.",
    },
    "th": {
        "PENDING":    "การ{ptype}ของคุณจำนวน {ccy} {amount} ผ่าน {method} อยู่ระหว่างดำเนินการ {notes}",
        "PROCESSING": "การ{ptype}ของคุณจำนวน {ccy} {amount} ผ่าน {method} กำลังถูกประมวลผล {notes}",
        "COMPLETED":  "การ{ptype}ของคุณจำนวน {ccy} {amount} ผ่าน {method} เสร็จสมบูรณ์แล้ว",
        "REJECTED":   "การ{ptype}ของคุณจำนวน {ccy} {amount} ผ่าน {method} ไม่ได้รับการดำเนินการ เหตุผล: {notes}",
        "BLOCKED":    "การ{ptype}ของคุณจำนวน {ccy} {amount} ผ่าน {method} ถูกระงับ เหตุผล: {notes}",
        "FAILED":     "การ{ptype}ของคุณจำนวน {ccy} {amount} ผ่าน {method} ล้มเหลว {notes} กรุณาลองใหม่หรือติดต่อฝ่ายสนับสนุน",
        "UNKNOWN":    "การ{ptype}ของคุณจำนวน {ccy} {amount} มีสถานะ: {status} กรุณาติดต่อฝ่ายสนับสนุนเพื่อรับข้อมูลเพิ่มเติม",
    },
    "id": {
        "PENDING":    "{ptype} Anda sebesar {ccy} {amount} melalui {method} sedang menunggu. {notes}",
        "PROCESSING": "{ptype} Anda sebesar {ccy} {amount} melalui {method} sedang diproses. {notes}",
        "COMPLETED":  "{ptype} Anda sebesar {ccy} {amount} melalui {method} telah berhasil diselesaikan.",
        "REJECTED":   "{ptype} Anda sebesar {ccy} {amount} melalui {method} tidak diproses. Alasan: {notes}",
        "BLOCKED":    "{ptype} Anda sebesar {ccy} {amount} melalui {method} telah diblokir. Alasan: {notes}",
        "FAILED":     "{ptype} Anda sebesar {ccy} {amount} melalui {method} gagal. {notes} Silakan coba lagi atau hubungi dukungan.",
        "UNKNOWN":    "{ptype} Anda sebesar {ccy} {amount} memiliki status: {status}. Silakan hubungi dukungan untuk informasi lebih lanjut.",
    },
    "ms": {
        "PENDING":    "{ptype} anda sebanyak {ccy} {amount} melalui {method} sedang menunggu. {notes}",
        "PROCESSING": "{ptype} anda sebanyak {ccy} {amount} melalui {method} sedang diproses. {notes}",
        "COMPLETED":  "{ptype} anda sebanyak {ccy} {amount} melalui {method} telah berjaya diselesaikan.",
        "REJECTED":   "{ptype} anda sebanyak {ccy} {amount} melalui {method} tidak diproses. Sebab: {notes}",
        "BLOCKED":    "{ptype} anda sebanyak {ccy} {amount} melalui {method} telah disekat. Sebab: {notes}",
        "FAILED":     "{ptype} anda sebanyak {ccy} {amount} melalui {method} gagal. {notes} Sila cuba lagi atau hubungi sokongan.",
        "UNKNOWN":    "{ptype} anda sebanyak {ccy} {amount} mempunyai status: {status}. Sila hubungi sokongan untuk maklumat lanjut.",
    },
    "vi": {
        "PENDING":    "{ptype} của bạn là {ccy} {amount} qua {method} đang chờ xử lý. {notes}",
        "PROCESSING": "{ptype} của bạn là {ccy} {amount} qua {method} đang được xử lý. {notes}",
        "COMPLETED":  "{ptype} của bạn là {ccy} {amount} qua {method} đã hoàn thành thành công.",
        "REJECTED":   "{ptype} của bạn là {ccy} {amount} qua {method} không được xử lý. Lý do: {notes}",
        "BLOCKED":    "{ptype} của bạn là {ccy} {amount} qua {method} đã bị chặn. Lý do: {notes}",
        "FAILED":     "{ptype} của bạn là {ccy} {amount} qua {method} thất bại. {notes} Vui lòng thử lại hoặc liên hệ hỗ trợ.",
        "UNKNOWN":    "{ptype} của bạn là {ccy} {amount} có trạng thái: {status}. Vui lòng liên hệ hỗ trợ để biết thêm chi tiết.",
    },
    "tl": {
        "PENDING":    "Ang iyong {ptype} na {ccy} {amount} sa pamamagitan ng {method} ay nakabinbin pa. {notes}",
        "PROCESSING": "Ang iyong {ptype} na {ccy} {amount} sa pamamagitan ng {method} ay pinoproseso na. {notes}",
        "COMPLETED":  "Ang iyong {ptype} na {ccy} {amount} sa pamamagitan ng {method} ay matagumpay na nakumpleto.",
        "REJECTED":   "Ang iyong {ptype} na {ccy} {amount} sa pamamagitan ng {method} ay hindi naproseso. Dahilan: {notes}",
        "BLOCKED":    "Ang iyong {ptype} na {ccy} {amount} sa pamamagitan ng {method} ay naharang. Dahilan: {notes}",
        "FAILED":     "Ang iyong {ptype} na {ccy} {amount} sa pamamagitan ng {method} ay nabigo. {notes} Pakisubukan muli o makipag-ugnayan sa suporta.",
        "UNKNOWN":    "Ang iyong {ptype} na {ccy} {amount} ay may status na: {status}. Makipag-ugnayan sa suporta para sa mga detalye.",
    },
}

# Localised payment type labels
PTYPE_I18N = {
    "en": {"withdrawal": "withdrawal",  "deposit": "deposit"},
    "th": {"withdrawal": "ถอนเงิน",      "deposit": "ฝากเงิน"},
    "id": {"withdrawal": "penarikan",   "deposit": "setoran"},
    "ms": {"withdrawal": "pengeluaran", "deposit": "deposit"},
    "vi": {"withdrawal": "rút tiền",    "deposit": "nạp tiền"},
    "tl": {"withdrawal": "withdrawal",  "deposit": "deposito"},
}


def lookup(message: str, user_id: str, lang: str = "en") -> dict:
    from app.db_init import get_connection
    normalised = message.lower()

    if any(e in normalised for e in PAYMENT_EXCLUSIONS):
        return {"matched": False, "response": ""}
    if not any(t in normalised for t in PAYMENT_TRIGGERS):
        return {"matched": False, "response": ""}

    conn   = get_connection()
    rows   = conn.execute(
        """SELECT * FROM payments WHERE user_id = ?
           ORDER BY updated_at DESC LIMIT 5""",
        (user_id,)
    ).fetchall()
    conn.close()

    if not rows:
        return {"matched": False, "response": ""}

    payments = [dict(r) for r in rows]

    # Filter to most relevant based on message keywords (EN + multilingual)
    withdrawal_words = ["withdrawal", "withdraw", "payout", "cashout",
                        "penarikan", "tarik", "rút tiền", "mag-withdraw",
                        "ถอนเงิน", "pengeluaran", "kailan darating"]
    deposit_words    = ["deposit", "top up", "topup", "add funds",
                        "setoran", "nạp tiền", "deposito", "ฝากเงิน"]

    if any(w in normalised for w in withdrawal_words):
        relevant = [p for p in payments if p["type"] == "withdrawal"]
    elif any(w in normalised for w in deposit_words):
        relevant = [p for p in payments if p["type"] == "deposit"]
    else:
        relevant = payments

    if not relevant:
        relevant = payments

    latest    = relevant[0]
    status    = latest["status"].upper()
    amount    = f"{latest['amount']:,.0f}"
    ccy       = latest["currency"]
    method    = latest["method"].replace("_", " ").title()
    notes     = latest["notes"] or ""
    ptype_key = latest["type"].lower()

    # Localised payment type label
    lang_ptypes = PTYPE_I18N.get(lang, PTYPE_I18N["en"])
    ptype = lang_ptypes.get(ptype_key, ptype_key)

    # Localised template — fall back to English if lang not found
    templates = STATUS_TEMPLATES.get(lang, STATUS_TEMPLATES["en"])
    template  = templates.get(status, templates["UNKNOWN"])

    response = template.format(
        ptype=ptype, ccy=ccy, amount=amount,
        method=method, notes=notes, status=status
    )

    return {"matched": True, "response": response}
