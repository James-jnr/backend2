import logging
import smtplib
from email.message import EmailMessage

import httpx

from . import config

log = logging.getLogger("notify")


def _telegram(text: str):
    if not (config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID):
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    for i in range(0, len(text), 3900):
        r = httpx.post(url, json={"chat_id": config.TELEGRAM_CHAT_ID, "text": text[i:i + 3900],
                                  "disable_web_page_preview": True}, timeout=15)
        if r.status_code != 200:
            log.error("Telegram error %s %s", r.status_code, r.text[:200])


def _email(subject: str, text: str):
    if not (config.SMTP_HOST and config.EMAIL_TO):
        return
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, config.EMAIL_FROM, config.EMAIL_TO
    msg.set_content(text)
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as s:
        s.starttls()
        if config.SMTP_USER:
            s.login(config.SMTP_USER, config.SMTP_PASS)
        s.send_message(msg)


def notify(subject: str, text: str):
    """Send to every configured channel; one channel failing never blocks the other."""
    log.info("ALERT: %s", subject)
    for fn, args in ((_telegram, (f"{subject}\n\n{text}",)), (_email, (subject, text))):
        try:
            fn(*args)
        except Exception:
            log.exception("delivery failed via %s", fn.__name__)
