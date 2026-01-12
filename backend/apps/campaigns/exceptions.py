"""Custom exceptions for campaigns app."""


class CampaignError(Exception):
    """Base exception for campaign operations."""

    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or 'campaign_error'
        super().__init__(self.message)


class CampaignNotFoundError(CampaignError):
    """Campaign does not exist."""

    def __init__(self, campaign_id: str = None):
        message = f"Campaign {campaign_id} not found" if campaign_id else "Campaign not found"
        super().__init__(message, code='campaign_not_found')


class CampaignNotEditableError(CampaignError):
    """Campaign cannot be modified in current state."""

    def __init__(self, status: str = None):
        message = f"Campaign cannot be edited in '{status}' status" if status else "Campaign is not editable"
        super().__init__(message, code='campaign_not_editable')


class CampaignAlreadyStartedError(CampaignError):
    """Campaign has already been started."""

    def __init__(self):
        super().__init__("Campaign has already been started", code='campaign_already_started')


class CampaignNotSendingError(CampaignError):
    """Campaign is not in sending state."""

    def __init__(self, action: str = "perform this action"):
        super().__init__(f"Campaign must be in sending state to {action}", code='campaign_not_sending')


class NoRecipientsError(CampaignError):
    """Campaign has no recipients."""

    def __init__(self):
        super().__init__("Campaign requires at least one recipient", code='no_recipients')


class DuplicateCampaignNameError(CampaignError):
    """Campaign name already exists in workspace."""

    def __init__(self, name: str = None):
        message = f"Campaign '{name}' already exists" if name else "Campaign name already exists"
        super().__init__(message, code='duplicate_campaign_name')


class EmailAccountNotConfiguredError(CampaignError):
    """No email account configured for campaign."""

    def __init__(self):
        super().__init__("No email account configured for this campaign", code='no_email_account')


class EmailAccountLimitReachedError(CampaignError):
    """Email account has reached sending limit."""

    def __init__(self):
        super().__init__("Email account has reached its daily sending limit", code='email_limit_reached')


class InvalidRecipientError(CampaignError):
    """Invalid recipient for campaign."""

    def __init__(self, reason: str = None):
        message = f"Invalid recipient: {reason}" if reason else "Invalid recipient"
        super().__init__(message, code='invalid_recipient')


class TemplateRenderError(CampaignError):
    """Error rendering email template."""

    def __init__(self, detail: str = None):
        message = f"Template rendering failed: {detail}" if detail else "Template rendering failed"
        super().__init__(message, code='template_render_error')
