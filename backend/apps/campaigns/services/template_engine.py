import re
import random
import html
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RenderResult:
    """Result of template rendering."""
    subject: str
    content_html: str
    content_text: str
    variables_used: List[str]
    missing_variables: List[str]
    spintax_variations: int


class TemplateEngine:
    """Engine for processing email templates with variables and spintax."""

    # Pattern for matching variables: {{variable}} or {{variable|fallback}}
    VARIABLE_PATTERN = re.compile(r'\{\{([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)(?:\|([^}]*))?\}\}')

    # Pattern for matching spintax: {option1|option2|option3}
    SPINTAX_PATTERN = re.compile(r'\{([^{}|]+(?:\|[^{}|]+)+)\}')

    # Standard contact variables
    CONTACT_VARIABLES = {
        'email': 'Contact email address',
        'first_name': 'Contact first name',
        'last_name': 'Contact last name',
        'full_name': 'Contact full name',
        'company': 'Contact company name',
        'job_title': 'Contact job title',
        'phone': 'Contact phone number',
        'website': 'Contact website',
        'linkedin_url': 'Contact LinkedIn URL',
        'twitter_handle': 'Contact Twitter handle',
        'city': 'Contact city',
        'state': 'Contact state/region',
        'country': 'Contact country',
        'timezone': 'Contact timezone',
    }

    # Sender variables
    SENDER_VARIABLES = {
        'sender_name': 'Sender full name',
        'sender_first_name': 'Sender first name',
        'sender_email': 'Sender email address',
        'sender_company': 'Sender company name',
        'sender_title': 'Sender job title',
        'sender_phone': 'Sender phone number',
    }

    # Campaign variables
    CAMPAIGN_VARIABLES = {
        'campaign_name': 'Campaign name',
        'unsubscribe_link': 'Unsubscribe URL',
        'view_in_browser_link': 'View in browser URL',
    }

    # Date/time variables
    DATE_VARIABLES = {
        'today': 'Current date',
        'current_month': 'Current month name',
        'current_year': 'Current year',
        'current_day': 'Current day of week',
    }

    def __init__(self):
        self.all_variables = {
            **self.CONTACT_VARIABLES,
            **self.SENDER_VARIABLES,
            **self.CAMPAIGN_VARIABLES,
            **self.DATE_VARIABLES,
        }

    def extract_variables(self, text: str) -> List[str]:
        """Extract all variable names from template text."""
        matches = self.VARIABLE_PATTERN.findall(text)
        return list(set(match[0] for match in matches))

    def extract_spintax(self, text: str) -> List[str]:
        """Extract all spintax patterns from template text."""
        return self.SPINTAX_PATTERN.findall(text)

    def has_spintax(self, text: str) -> bool:
        """Check if text contains spintax."""
        return bool(self.SPINTAX_PATTERN.search(text))

    def count_spintax_variations(self, text: str) -> int:
        """Calculate total number of possible spintax variations."""
        patterns = self.extract_spintax(text)
        if not patterns:
            return 1

        variations = 1
        for pattern in patterns:
            options = pattern.split('|')
            variations *= len(options)
        return variations

    def process_spintax(self, text: str, seed: Optional[int] = None) -> str:
        """
        Process spintax in text, randomly selecting options.

        Example: "Hello {there|friend|buddy}" -> "Hello friend"
        """
        if seed is not None:
            random.seed(seed)

        def replace_spintax(match):
            options = match.group(1).split('|')
            return random.choice(options)

        return self.SPINTAX_PATTERN.sub(replace_spintax, text)

    def process_variables(
        self,
        text: str,
        context: Dict[str, Any],
        escape_html: bool = False
    ) -> Tuple[str, List[str], List[str]]:
        """
        Replace variables in text with values from context.

        Returns: (processed_text, variables_used, missing_variables)
        """
        variables_used = []
        missing_variables = []

        def replace_variable(match):
            var_name = match.group(1)
            fallback = match.group(2)

            # Handle nested variables like custom_fields.field_name
            value = self._get_nested_value(context, var_name)

            if value is not None:
                variables_used.append(var_name)
                str_value = str(value)
                if escape_html:
                    str_value = html.escape(str_value)
                return str_value
            elif fallback is not None:
                # Use fallback value
                variables_used.append(var_name)
                return fallback
            else:
                # Keep original placeholder if no value and no fallback
                missing_variables.append(var_name)
                return match.group(0)

        processed = self.VARIABLE_PATTERN.sub(replace_variable, text)
        return processed, list(set(variables_used)), list(set(missing_variables))

    def _get_nested_value(self, context: Dict[str, Any], key: str) -> Optional[Any]:
        """Get a nested value from context using dot notation."""
        parts = key.split('.')
        value = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

            if value is None:
                return None

        return value

    def render(
        self,
        subject: str,
        content_html: str,
        content_text: str,
        context: Dict[str, Any],
        process_spintax: bool = True,
        spintax_seed: Optional[int] = None
    ) -> RenderResult:
        """
        Fully render a template with variables and spintax.

        Args:
            subject: Email subject template
            content_html: HTML content template
            content_text: Plain text content template
            context: Variable values
            process_spintax: Whether to process spintax
            spintax_seed: Seed for reproducible spintax selection
        """
        # Calculate spintax variations before processing
        spintax_variations = max(
            self.count_spintax_variations(subject),
            self.count_spintax_variations(content_html),
            self.count_spintax_variations(content_text)
        )

        # Process spintax first (if enabled)
        if process_spintax:
            subject = self.process_spintax(subject, spintax_seed)
            content_html = self.process_spintax(content_html, spintax_seed)
            content_text = self.process_spintax(content_text, spintax_seed)

        # Process variables
        subject, subj_used, subj_missing = self.process_variables(subject, context)
        content_html, html_used, html_missing = self.process_variables(
            content_html, context, escape_html=True
        )
        content_text, text_used, text_missing = self.process_variables(content_text, context)

        # Combine results
        all_used = list(set(subj_used + html_used + text_used))
        all_missing = list(set(subj_missing + html_missing + text_missing))

        return RenderResult(
            subject=subject,
            content_html=content_html,
            content_text=content_text,
            variables_used=all_used,
            missing_variables=all_missing,
            spintax_variations=spintax_variations
        )

    def preview(
        self,
        subject: str,
        content_html: str,
        content_text: str,
        sample_contact: Optional[Dict[str, Any]] = None
    ) -> RenderResult:
        """
        Generate a preview of the template with sample data.
        """
        # Default sample data
        context = {
            'email': 'john.doe@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'full_name': 'John Doe',
            'company': 'Acme Corp',
            'job_title': 'Marketing Manager',
            'phone': '+1 (555) 123-4567',
            'website': 'https://example.com',
            'linkedin_url': 'https://linkedin.com/in/johndoe',
            'twitter_handle': '@johndoe',
            'city': 'San Francisco',
            'state': 'California',
            'country': 'United States',
            'timezone': 'America/Los_Angeles',
            'sender_name': 'Jane Smith',
            'sender_first_name': 'Jane',
            'sender_email': 'jane@mycompany.com',
            'sender_company': 'My Company',
            'sender_title': 'Sales Representative',
            'sender_phone': '+1 (555) 987-6543',
            'campaign_name': 'Q1 Outreach',
            'unsubscribe_link': 'https://example.com/unsubscribe',
            'view_in_browser_link': 'https://example.com/view',
            'today': 'January 11, 2026',
            'current_month': 'January',
            'current_year': '2026',
            'current_day': 'Saturday',
            'custom_fields': {},
        }

        # Override with sample contact if provided
        if sample_contact:
            context.update(sample_contact)

        return self.render(
            subject=subject,
            content_html=content_html,
            content_text=content_text,
            context=context,
            process_spintax=True,
            spintax_seed=42  # Fixed seed for consistent previews
        )

    def validate_template(
        self,
        subject: str,
        content_html: str,
        content_text: str
    ) -> Dict[str, Any]:
        """
        Validate a template and return analysis.
        """
        # Extract all variables
        all_vars = set()
        all_vars.update(self.extract_variables(subject))
        all_vars.update(self.extract_variables(content_html))
        all_vars.update(self.extract_variables(content_text))

        # Categorize variables
        known_vars = []
        custom_vars = []
        for var in all_vars:
            if var in self.all_variables or var.startswith('custom_fields.'):
                known_vars.append(var)
            else:
                custom_vars.append(var)

        # Check for spintax
        has_spintax = (
            self.has_spintax(subject) or
            self.has_spintax(content_html) or
            self.has_spintax(content_text)
        )

        spintax_count = (
            len(self.extract_spintax(subject)) +
            len(self.extract_spintax(content_html)) +
            len(self.extract_spintax(content_text))
        )

        variations = max(
            self.count_spintax_variations(subject),
            self.count_spintax_variations(content_html),
            self.count_spintax_variations(content_text)
        )

        return {
            'is_valid': True,
            'variables': list(all_vars),
            'known_variables': known_vars,
            'custom_variables': custom_vars,
            'has_spintax': has_spintax,
            'spintax_count': spintax_count,
            'spintax_variations': variations,
            'warnings': [],
        }

    def html_to_text(self, html_content: str) -> str:
        """
        Convert HTML content to plain text.
        """
        # Remove HTML tags
        text = re.sub(r'<br\s*/?>', '\n', html_content)
        text = re.sub(r'<p[^>]*>', '\n\n', text)
        text = re.sub(r'</p>', '', text)
        text = re.sub(r'<div[^>]*>', '\n', text)
        text = re.sub(r'</div>', '', text)
        text = re.sub(r'<li[^>]*>', '\n• ', text)
        text = re.sub(r'<[^>]+>', '', text)

        # Decode HTML entities
        text = html.unescape(text)

        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()

        return text

    def get_available_variables(self) -> Dict[str, Dict[str, str]]:
        """Get all available variables organized by category."""
        return {
            'contact': self.CONTACT_VARIABLES,
            'sender': self.SENDER_VARIABLES,
            'campaign': self.CAMPAIGN_VARIABLES,
            'date': self.DATE_VARIABLES,
        }
