"""Email notifier via SendGrid."""
from __future__ import annotations

import logging
from typing import Any

from src.integrations.base import BaseIntegration
from src.integrations.registry import IntegrationRegistry

logger = logging.getLogger(__name__)


@IntegrationRegistry.register("email")
class EmailIntegration(BaseIntegration):
    """Send emails via SendGrid."""

    async def initialize(self) -> None:
        self._require("api_key", "from_email")
        self._mark_ready()
        logger.info("Email (SendGrid) integration ready")

    async def shutdown(self) -> None:
        pass

    async def send(
        self,
        to_email: str,
        subject: str,
        body: str,
        *,
        html: bool = False,
    ) -> None:
        try:
            import sendgrid
            from sendgrid.helpers.mail import Content, Email, Mail, To
        except ImportError as exc:
            raise ImportError("Run: uv add sendgrid") from exc

        sg = sendgrid.SendGridAPIClient(api_key=self.config["api_key"])
        from_name = self.config.get("from_name", "AI Tutor")
        content_type = "text/html" if html else "text/plain"

        message = Mail(
            from_email=Email(self.config["from_email"], from_name),
            to_emails=To(to_email),
            subject=subject,
            plain_text_content=Content(content_type, body),
        )

        response = sg.client.mail.send.post(request_body=message.get())
        if response.status_code not in (200, 202):
            raise RuntimeError(
                f"SendGrid returned status {response.status_code}: {response.body}"
            )
        logger.info("Email sent to %s", to_email)
