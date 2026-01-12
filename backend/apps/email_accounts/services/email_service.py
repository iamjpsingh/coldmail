import smtplib
import imaplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
from dataclasses import dataclass

from django.utils import timezone

from apps.email_accounts.models import EmailAccount, EmailAccountLog


@dataclass
class ConnectionResult:
    """Result of a connection test."""
    success: bool
    message: str
    details: dict = None


@dataclass
class SendResult:
    """Result of sending an email."""
    success: bool
    message: str
    message_id: Optional[str] = None


class EmailService:
    """Service for managing email operations."""

    def __init__(self, email_account: EmailAccount):
        self.account = email_account

    def test_smtp_connection(self) -> ConnectionResult:
        """Test SMTP connection."""
        try:
            if self.account.smtp_use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    self.account.smtp_host,
                    self.account.smtp_port,
                    context=context,
                    timeout=30
                )
            else:
                server = smtplib.SMTP(
                    self.account.smtp_host,
                    self.account.smtp_port,
                    timeout=30
                )
                if self.account.smtp_use_tls:
                    server.starttls()

            server.login(self.account.smtp_username, self.account.smtp_password)
            server.quit()

            # Update account status
            self.account.last_connection_test = timezone.now()
            self.account.last_connection_success = True
            self.account.last_connection_error = ''
            self.account.status = EmailAccount.Status.ACTIVE
            self.account.save(update_fields=[
                'last_connection_test', 'last_connection_success',
                'last_connection_error', 'status'
            ])

            # Log success
            self._log(
                EmailAccountLog.LogType.CONNECTION_TEST,
                "SMTP connection successful",
                is_success=True
            )

            return ConnectionResult(
                success=True,
                message="SMTP connection successful"
            )

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Authentication failed: {str(e)}"
            self._handle_connection_error(error_msg)
            return ConnectionResult(success=False, message=error_msg)

        except smtplib.SMTPConnectError as e:
            error_msg = f"Connection failed: {str(e)}"
            self._handle_connection_error(error_msg)
            return ConnectionResult(success=False, message=error_msg)

        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            self._handle_connection_error(error_msg)
            return ConnectionResult(success=False, message=error_msg)

    def test_imap_connection(self) -> ConnectionResult:
        """Test IMAP connection."""
        if not self.account.imap_host:
            return ConnectionResult(
                success=False,
                message="IMAP not configured"
            )

        try:
            if self.account.imap_use_ssl:
                server = imaplib.IMAP4_SSL(
                    self.account.imap_host,
                    self.account.imap_port
                )
            else:
                server = imaplib.IMAP4(
                    self.account.imap_host,
                    self.account.imap_port
                )

            server.login(
                self.account.imap_username or self.account.smtp_username,
                self.account.imap_password or self.account.smtp_password
            )
            server.logout()

            self._log(
                EmailAccountLog.LogType.CONNECTION_TEST,
                "IMAP connection successful",
                is_success=True
            )

            return ConnectionResult(
                success=True,
                message="IMAP connection successful"
            )

        except Exception as e:
            error_msg = f"IMAP connection error: {str(e)}"
            self._log(
                EmailAccountLog.LogType.CONNECTION_TEST,
                error_msg,
                is_success=False
            )
            return ConnectionResult(success=False, message=error_msg)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        reply_to: Optional[str] = None,
        headers: Optional[dict] = None
    ) -> SendResult:
        """Send an email."""

        # Check if can send
        if not self.account.can_send:
            self._log(
                EmailAccountLog.LogType.LIMIT_REACHED,
                "Cannot send: limit reached or account not active",
                is_success=False
            )
            return SendResult(
                success=False,
                message="Cannot send: limit reached or account not active"
            )

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.account.from_name} <{self.account.email}>" if self.account.from_name else self.account.email
            msg['To'] = to_email
            msg['Reply-To'] = reply_to or self.account.reply_to or self.account.email

            # Add custom headers
            if headers:
                for key, value in headers.items():
                    msg[key] = value

            # Add body
            if text_body:
                msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            # Connect and send
            if self.account.smtp_use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    self.account.smtp_host,
                    self.account.smtp_port,
                    context=context,
                    timeout=30
                )
            else:
                server = smtplib.SMTP(
                    self.account.smtp_host,
                    self.account.smtp_port,
                    timeout=30
                )
                if self.account.smtp_use_tls:
                    server.starttls()

            server.login(self.account.smtp_username, self.account.smtp_password)
            server.sendmail(self.account.email, [to_email], msg.as_string())
            server.quit()

            # Update counters
            self.account.increment_sent_count()

            # Log success
            self._log(
                EmailAccountLog.LogType.EMAIL_SENT,
                f"Email sent to {to_email}",
                details={'to': to_email, 'subject': subject},
                is_success=True
            )

            return SendResult(
                success=True,
                message="Email sent successfully",
                message_id=msg.get('Message-ID')
            )

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            self._log(
                EmailAccountLog.LogType.EMAIL_FAILED,
                error_msg,
                details={'to': to_email, 'subject': subject, 'error': str(e)},
                is_success=False
            )
            return SendResult(success=False, message=error_msg)

    def _handle_connection_error(self, error_msg: str):
        """Handle connection error."""
        self.account.last_connection_test = timezone.now()
        self.account.last_connection_success = False
        self.account.last_connection_error = error_msg
        self.account.status = EmailAccount.Status.ERROR
        self.account.save(update_fields=[
            'last_connection_test', 'last_connection_success',
            'last_connection_error', 'status'
        ])

        self._log(
            EmailAccountLog.LogType.CONNECTION_TEST,
            error_msg,
            is_success=False
        )

    def _log(
        self,
        log_type: str,
        message: str,
        details: dict = None,
        is_success: bool = True
    ):
        """Create a log entry."""
        EmailAccountLog.objects.create(
            email_account=self.account,
            log_type=log_type,
            message=message,
            details=details or {},
            is_success=is_success
        )
