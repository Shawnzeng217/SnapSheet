"""
Email Service / 邮件发送服务
通过SMTP发送OCR结果Excel附件
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os

from app.config import settings


class EmailService:
    """邮件发送服务"""

    async def send_result(self, to_email: str, file_path: str) -> None:
        """
        发送OCR结果Excel文件到指定邮箱
        Send OCR result Excel file to specified email
        """
        if not settings.smtp_user or not settings.smtp_password:
            raise RuntimeError("SMTP not configured. Please set SMTP_* environment variables.")

        msg = MIMEMultipart()
        msg["From"] = settings.smtp_from or settings.smtp_user
        msg["To"] = to_email
        msg["Subject"] = "Hotel OCR Result - 酒店表单识别结果"

        body = (
            "您好，\n\n"
            "附件是OCR识别生成的Excel文件，请查收。\n"
            "如有识别错误，请在Excel中手动修正。\n\n"
            "Hello,\n\n"
            "Please find the OCR result Excel file attached.\n"
            "If there are recognition errors, please correct them manually in Excel.\n\n"
            "— Hotel OCR System"
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Attach Excel file
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            part = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)

        # Send via SMTP (run in thread to not block async loop)
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._smtp_send, msg, to_email)

    def _smtp_send(self, msg: MIMEMultipart, to_email: str) -> None:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from or settings.smtp_user, [to_email], msg.as_string())
