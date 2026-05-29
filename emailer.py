"""브리핑 HTML을 이메일로 발송한다.

필요한 환경변수:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
  EMAIL_FROM (생략 시 SMTP_USER), EMAIL_TO (쉼표로 여러 명 가능)
"""

import os
import smtplib
import ssl
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr


def email_configured():
    """이메일 발송에 필요한 환경변수가 모두 있는지 확인한다."""
    required = ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "EMAIL_TO")
    return all(os.environ.get(key) for key in required)


def send_email(html, subject):
    """HTML 본문을 이메일로 발송한다."""
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    sender = os.environ.get("EMAIL_FROM", user)
    recipients = [addr.strip() for addr in os.environ["EMAIL_TO"].split(",") if addr.strip()]

    message = MIMEText(html, "html", "utf-8")
    message["Subject"] = Header(subject, "utf-8")
    message["From"] = formataddr(("아침 뉴스 브리핑", sender))
    message["To"] = ", ".join(recipients)

    context = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(user, password)
            server.sendmail(sender, recipients, message.as_string())
    else:
        with smtplib.SMTP(host, port) as server:
            server.starttls(context=context)
            server.login(user, password)
            server.sendmail(sender, recipients, message.as_string())
