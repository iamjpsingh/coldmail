import secrets
import logging
from typing import Optional
from urllib.parse import urljoin
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from apps.tracking.models import (
    WebsiteTrackingScript,
    WebsiteVisitor,
    VisitorSession,
    PageView,
    WebsiteEvent,
    VisitorIdentification,
)

logger = logging.getLogger(__name__)


class WebsiteTrackingService:
    """Service for website visitor tracking operations."""

    def __init__(self, base_url: Optional[str] = None):
        """Initialize website tracking service.

        Args:
            base_url: Base URL for tracking endpoints (defaults to settings)
        """
        self.base_url = base_url or getattr(
            settings, 'TRACKING_BASE_URL',
            getattr(settings, 'BASE_URL', 'http://localhost:8000')
        )

    # ==================== Script Management ====================

    def get_or_create_tracking_script(self, workspace) -> WebsiteTrackingScript:
        """Get or create the tracking script configuration for a workspace.

        Args:
            workspace: Workspace instance

        Returns:
            WebsiteTrackingScript instance
        """
        script, created = WebsiteTrackingScript.objects.get_or_create(
            workspace=workspace
        )
        if created:
            logger.info(f"Created tracking script for workspace {workspace.id}")
        return script

    def generate_tracking_snippet(self, script: WebsiteTrackingScript) -> str:
        """Generate the JavaScript tracking snippet to embed on websites.

        Args:
            script: WebsiteTrackingScript instance

        Returns:
            JavaScript code snippet as string
        """
        api_endpoint = urljoin(self.base_url, '/t/w/')

        return f'''<!-- ColdMail Website Tracking -->
<script>
(function(w,d,s,id){{
  // Initialize tracking object
  w.ColdMail=w.ColdMail||{{}};
  w.ColdMail.q=w.ColdMail.q||[];
  w.ColdMail.scriptId='{script.script_id}';
  w.ColdMail.endpoint='{api_endpoint}';

  // Get or set visitor ID
  var visitorId=localStorage.getItem('cm_vid');
  if(!visitorId){{
    visitorId='v_'+Math.random().toString(36).substr(2,9)+Date.now().toString(36);
    localStorage.setItem('cm_vid',visitorId);
  }}
  w.ColdMail.visitorId=visitorId;

  // Get or set session ID (expires after {script.session_timeout_minutes} minutes of inactivity)
  var sessionTimeout={script.session_timeout_minutes}*60*1000;
  var lastActivity=parseInt(localStorage.getItem('cm_last')||'0');
  var sessionId=localStorage.getItem('cm_sid');
  var now=Date.now();

  if(!sessionId||now-lastActivity>sessionTimeout){{
    sessionId='s_'+Math.random().toString(36).substr(2,9)+now.toString(36);
    localStorage.setItem('cm_sid',sessionId);
    w.ColdMail.isNewSession=true;
  }}
  localStorage.setItem('cm_last',now.toString());
  w.ColdMail.sessionId=sessionId;

  // Parse UTM params
  var params=new URLSearchParams(window.location.search);
  w.ColdMail.utm={{
    source:params.get('utm_source')||'',
    medium:params.get('utm_medium')||'',
    campaign:params.get('utm_campaign')||'',
    term:params.get('utm_term')||'',
    content:params.get('utm_content')||''
  }};

  // Check for email identification token
  var cmt=params.get('cmt');
  if(cmt){{
    w.ColdMail.identToken=cmt;
    // Remove token from URL without reload
    params.delete('cmt');
    var newUrl=window.location.pathname+(params.toString()?'?'+params.toString():'')+window.location.hash;
    history.replaceState(null,'',newUrl);
  }}

  // Track function
  w.ColdMail.track=function(eventType,data){{
    var payload={{
      script_id:w.ColdMail.scriptId,
      visitor_id:w.ColdMail.visitorId,
      session_id:w.ColdMail.sessionId,
      event_type:eventType,
      page_url:window.location.href,
      page_path:window.location.pathname,
      page_title:document.title,
      referrer:document.referrer,
      screen_resolution:screen.width+'x'+screen.height,
      utm:w.ColdMail.utm,
      timestamp:new Date().toISOString()
    }};
    if(w.ColdMail.identToken)payload.ident_token=w.ColdMail.identToken;
    if(data)Object.assign(payload,data);

    // Send via beacon or fetch
    var url=w.ColdMail.endpoint+'track';
    var body=JSON.stringify(payload);
    if(navigator.sendBeacon){{
      navigator.sendBeacon(url,body);
    }}else{{
      fetch(url,{{method:'POST',body:body,headers:{{'Content-Type':'application/json'}},keepalive:true}});
    }}
  }};

  // Identify visitor
  w.ColdMail.identify=function(email,properties){{
    w.ColdMail.track('identify',{{email:email,properties:properties||{{}}}});
  }};

  // Track custom event
  w.ColdMail.event=function(eventName,properties){{
    w.ColdMail.track('custom',{{event_name:eventName,properties:properties||{{}}}});
  }};

  // Auto-track page view
  {f"w.ColdMail.track('page_view');" if script.track_page_views else "// Page view tracking disabled"}

  // Track session start if new session
  if(w.ColdMail.isNewSession){{
    w.ColdMail.track('session_start');
  }}

  {self._generate_click_tracking(script) if script.track_clicks else "// Click tracking disabled"}

  {self._generate_form_tracking(script) if script.track_forms else "// Form tracking disabled"}

  {self._generate_scroll_tracking(script) if script.track_scroll_depth else "// Scroll tracking disabled"}

  {self._generate_time_tracking(script) if script.track_time_on_page else "// Time tracking disabled"}

  // Track page visibility changes
  document.addEventListener('visibilitychange',function(){{
    if(document.visibilityState==='hidden'){{
      localStorage.setItem('cm_last',Date.now().toString());
    }}
  }});

}})(window,document,'script','coldmail-tracker');
</script>
<!-- End ColdMail Website Tracking -->'''

    def _generate_click_tracking(self, script: WebsiteTrackingScript) -> str:
        """Generate click tracking JavaScript."""
        return '''
  // Track clicks
  document.addEventListener('click',function(e){
    var target=e.target.closest('a,button,[data-cm-track]');
    if(!target)return;

    var data={
      element_tag:target.tagName.toLowerCase(),
      element_id:target.id||'',
      element_class:target.className||'',
      element_text:(target.textContent||'').slice(0,100).trim()
    };

    if(target.tagName==='A'){
      data.target_url=target.href||'';
      // Track outbound links separately
      if(target.hostname&&target.hostname!==window.location.hostname){
        w.ColdMail.track('outbound_link',data);
        return;
      }
    }

    if(target.hasAttribute('data-cm-track')){
      data.event_name=target.getAttribute('data-cm-track');
    }

    w.ColdMail.track('click',data);
  },true);'''

    def _generate_form_tracking(self, script: WebsiteTrackingScript) -> str:
        """Generate form tracking JavaScript."""
        return '''
  // Track forms
  document.addEventListener('submit',function(e){
    var form=e.target;
    if(form.tagName!=='FORM')return;

    var data={
      form_id:form.id||'',
      form_name:form.name||'',
      form_action:form.action||''
    };

    // Try to get email from form fields
    var emailField=form.querySelector('input[type="email"],input[name*="email"]');
    if(emailField&&emailField.value){
      w.ColdMail.identify(emailField.value);
    }

    w.ColdMail.track('form_submit',data);
  },true);

  // Track form start (first interaction)
  var formStartTracked=new WeakSet();
  document.addEventListener('focus',function(e){
    var form=e.target.closest('form');
    if(!form||formStartTracked.has(form))return;
    formStartTracked.add(form);

    w.ColdMail.track('form_start',{
      form_id:form.id||'',
      form_name:form.name||''
    });
  },true);'''

    def _generate_scroll_tracking(self, script: WebsiteTrackingScript) -> str:
        """Generate scroll depth tracking JavaScript."""
        return '''
  // Track scroll depth
  var maxScrollDepth=0;
  var scrollThresholds=[25,50,75,90,100];
  var scrollTracked=new Set();

  function getScrollDepth(){
    var scrollTop=window.pageYOffset||document.documentElement.scrollTop;
    var docHeight=Math.max(document.body.scrollHeight,document.documentElement.scrollHeight);
    var winHeight=window.innerHeight;
    return Math.round((scrollTop/(docHeight-winHeight))*100)||0;
  }

  var scrollTimeout;
  window.addEventListener('scroll',function(){
    clearTimeout(scrollTimeout);
    scrollTimeout=setTimeout(function(){
      var depth=getScrollDepth();
      if(depth>maxScrollDepth)maxScrollDepth=depth;

      scrollThresholds.forEach(function(threshold){
        if(depth>=threshold&&!scrollTracked.has(threshold)){
          scrollTracked.add(threshold);
          w.ColdMail.track('scroll',{scroll_depth:threshold});
        }
      });
    },100);
  });'''

    def _generate_time_tracking(self, script: WebsiteTrackingScript) -> str:
        """Generate time on page tracking JavaScript."""
        return '''
  // Track time on page
  var pageStartTime=Date.now();
  var totalActiveTime=0;
  var lastActiveTime=pageStartTime;
  var isActive=true;

  document.addEventListener('visibilitychange',function(){
    if(document.visibilityState==='hidden'){
      if(isActive){
        totalActiveTime+=Date.now()-lastActiveTime;
        isActive=false;
      }
    }else{
      lastActiveTime=Date.now();
      isActive=true;
    }
  });

  window.addEventListener('beforeunload',function(){
    if(isActive){
      totalActiveTime+=Date.now()-lastActiveTime;
    }
    var timeOnPage=Math.round(totalActiveTime/1000);
    if(timeOnPage>0){
      w.ColdMail.track('page_exit',{time_on_page:timeOnPage,max_scroll:maxScrollDepth||0});
    }
  });'''

    def get_minified_snippet(self, script: WebsiteTrackingScript) -> str:
        """Generate a minified version of the tracking snippet.

        Args:
            script: WebsiteTrackingScript instance

        Returns:
            Minified JavaScript code
        """
        # For production, you would use a proper JS minifier
        # This is a simplified version
        snippet = self.generate_tracking_snippet(script)
        # Remove comments and extra whitespace
        import re
        # Remove multi-line comments
        snippet = re.sub(r'/\*.*?\*/', '', snippet, flags=re.DOTALL)
        # Remove single-line comments (but not URLs)
        snippet = re.sub(r'(?<!:)//.*$', '', snippet, flags=re.MULTILINE)
        # Remove extra whitespace
        snippet = re.sub(r'\s+', ' ', snippet)
        return snippet.strip()

    # ==================== Visitor Management ====================

    @transaction.atomic
    def record_page_view(
        self,
        script_id: str,
        visitor_id: str,
        session_id: str,
        page_url: str,
        page_path: str,
        page_title: str = '',
        referrer: str = '',
        utm_params: dict = None,
        screen_resolution: str = '',
        ip_address: str = None,
        user_agent: str = '',
        ident_token: str = None,
    ) -> Optional[PageView]:
        """Record a page view event.

        Args:
            script_id: Tracking script ID
            visitor_id: Client-side visitor ID
            session_id: Client-side session ID
            page_url: Full page URL
            page_path: Page path
            page_title: Page title
            referrer: Referrer URL
            utm_params: UTM parameters dict
            screen_resolution: Screen resolution string
            ip_address: Client IP address
            user_agent: User agent string
            ident_token: Email identification token (from email link)

        Returns:
            PageView instance if recorded, None if invalid
        """
        try:
            script = WebsiteTrackingScript.objects.select_related('workspace').get(
                script_id=script_id,
                is_enabled=True
            )
        except WebsiteTrackingScript.DoesNotExist:
            logger.warning(f"Invalid or disabled tracking script: {script_id}")
            return None

        workspace = script.workspace
        utm_params = utm_params or {}

        # Get or create visitor
        visitor, created = WebsiteVisitor.objects.get_or_create(
            workspace=workspace,
            visitor_id=visitor_id,
            defaults={
                'first_page_url': page_url,
                'first_referrer': referrer,
                'utm_source': utm_params.get('source', ''),
                'utm_medium': utm_params.get('medium', ''),
                'utm_campaign': utm_params.get('campaign', ''),
                'utm_term': utm_params.get('term', ''),
                'utm_content': utm_params.get('content', ''),
                'ip_address': ip_address,
                'screen_resolution': screen_resolution,
            }
        )

        # Update visitor
        if not created:
            visitor.last_page_url = page_url
            visitor.last_seen_at = timezone.now()
            visitor.total_page_views += 1
            visitor.save(update_fields=['last_page_url', 'last_seen_at', 'total_page_views', 'updated_at'])

        # Parse user agent for device info
        device_info = self._parse_user_agent(user_agent)
        if created:
            visitor.device_type = device_info.get('device_type', '')
            visitor.browser_name = device_info.get('browser_name', '')
            visitor.browser_version = device_info.get('browser_version', '')
            visitor.os_name = device_info.get('os_name', '')
            visitor.os_version = device_info.get('os_version', '')
            visitor.save()

        # Get or create session
        session, session_created = VisitorSession.objects.get_or_create(
            visitor=visitor,
            session_id=session_id,
            defaults={
                'entry_page': page_url,
                'referrer': referrer,
                'utm_source': utm_params.get('source', ''),
                'utm_medium': utm_params.get('medium', ''),
                'utm_campaign': utm_params.get('campaign', ''),
                'ip_address': ip_address,
                'user_agent': user_agent,
            }
        )

        if session_created:
            visitor.total_sessions += 1
            visitor.save(update_fields=['total_sessions', 'updated_at'])

        # Update session
        session.exit_page = page_url
        session.page_views += 1
        session.is_active = True
        session.save(update_fields=['exit_page', 'page_views', 'is_active', 'updated_at'])

        # Create page view
        page_view = PageView.objects.create(
            visitor=visitor,
            session=session,
            page_url=page_url,
            page_path=page_path,
            page_title=page_title,
            referrer=referrer,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Handle identification token from email
        if ident_token:
            self._process_identification_token(visitor, ident_token)

        # Award score for page view
        if script.award_score_on_visit and visitor.contact:
            self._award_score(
                visitor.contact,
                script.page_view_score_points,
                'page_view',
                page_view
            )

        logger.debug(f"Recorded page view for visitor {visitor_id[:8]}...")
        return page_view

    @transaction.atomic
    def record_event(
        self,
        script_id: str,
        visitor_id: str,
        session_id: str,
        event_type: str,
        page_url: str,
        page_path: str,
        event_name: str = '',
        properties: dict = None,
        element_id: str = '',
        element_class: str = '',
        element_text: str = '',
        target_url: str = '',
        ip_address: str = None,
        user_agent: str = '',
    ) -> Optional[WebsiteEvent]:
        """Record a website event.

        Args:
            Various event parameters

        Returns:
            WebsiteEvent instance if recorded, None if invalid
        """
        try:
            script = WebsiteTrackingScript.objects.select_related('workspace').get(
                script_id=script_id,
                is_enabled=True
            )
        except WebsiteTrackingScript.DoesNotExist:
            logger.warning(f"Invalid or disabled tracking script: {script_id}")
            return None

        workspace = script.workspace

        # Get visitor and session
        try:
            visitor = WebsiteVisitor.objects.get(
                workspace=workspace,
                visitor_id=visitor_id
            )
        except WebsiteVisitor.DoesNotExist:
            # Create visitor if doesn't exist (edge case)
            visitor = WebsiteVisitor.objects.create(
                workspace=workspace,
                visitor_id=visitor_id,
                first_page_url=page_url,
                ip_address=ip_address,
            )

        try:
            session = VisitorSession.objects.get(
                visitor=visitor,
                session_id=session_id
            )
        except VisitorSession.DoesNotExist:
            session = VisitorSession.objects.create(
                visitor=visitor,
                session_id=session_id,
                entry_page=page_url,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        # Map event type to choices
        event_type_map = {
            'click': WebsiteEvent.EventType.CLICK,
            'form_submit': WebsiteEvent.EventType.FORM_SUBMIT,
            'form_start': WebsiteEvent.EventType.FORM_START,
            'scroll': WebsiteEvent.EventType.SCROLL,
            'video_play': WebsiteEvent.EventType.VIDEO_PLAY,
            'video_complete': WebsiteEvent.EventType.VIDEO_COMPLETE,
            'download': WebsiteEvent.EventType.DOWNLOAD,
            'outbound_link': WebsiteEvent.EventType.OUTBOUND_LINK,
            'custom': WebsiteEvent.EventType.CUSTOM,
        }

        event_type_choice = event_type_map.get(event_type, WebsiteEvent.EventType.CUSTOM)

        # Create event
        event = WebsiteEvent.objects.create(
            visitor=visitor,
            session=session,
            event_type=event_type_choice,
            event_name=event_name,
            page_url=page_url,
            page_path=page_path,
            element_id=element_id,
            element_class=element_class,
            element_text=element_text[:512] if element_text else '',
            target_url=target_url,
            properties=properties or {},
        )

        logger.debug(f"Recorded {event_type} event for visitor {visitor_id[:8]}...")
        return event

    @transaction.atomic
    def identify_visitor(
        self,
        script_id: str,
        visitor_id: str,
        email: str,
        properties: dict = None,
        method: str = 'form_submit',
        source: str = '',
    ) -> Optional[WebsiteVisitor]:
        """Identify a visitor by email address.

        Args:
            script_id: Tracking script ID
            visitor_id: Client-side visitor ID
            email: Email address to identify with
            properties: Additional properties
            method: Identification method
            source: Source of identification

        Returns:
            WebsiteVisitor instance if identified, None if invalid
        """
        try:
            script = WebsiteTrackingScript.objects.select_related('workspace').get(
                script_id=script_id,
                is_enabled=True
            )
        except WebsiteTrackingScript.DoesNotExist:
            logger.warning(f"Invalid or disabled tracking script: {script_id}")
            return None

        workspace = script.workspace

        # Get visitor
        try:
            visitor = WebsiteVisitor.objects.get(
                workspace=workspace,
                visitor_id=visitor_id
            )
        except WebsiteVisitor.DoesNotExist:
            logger.warning(f"Visitor not found: {visitor_id}")
            return None

        # Find or create contact
        from apps.contacts.models import Contact

        contact, created = Contact.objects.get_or_create(
            workspace=workspace,
            email=email.lower(),
            defaults={
                'source': 'website',
            }
        )

        # Update contact with properties if provided
        if properties:
            if properties.get('first_name'):
                contact.first_name = properties['first_name']
            if properties.get('last_name'):
                contact.last_name = properties['last_name']
            if properties.get('company'):
                contact.company = properties['company']
            contact.save()

        # Update visitor
        visitor.contact = contact
        visitor.is_identified = True
        visitor.identified_at = timezone.now()
        visitor.identification_method = method
        visitor.save(update_fields=[
            'contact', 'is_identified', 'identified_at',
            'identification_method', 'updated_at'
        ])

        # Create identification record
        VisitorIdentification.objects.create(
            visitor=visitor,
            contact=contact,
            method=method,
            email=email.lower(),
            source=source,
            metadata=properties or {},
        )

        # Award score for new session identification
        if script.award_score_on_visit:
            self._award_score(
                contact,
                script.visit_score_points,
                'website_visit',
                visitor
            )

        logger.info(f"Identified visitor {visitor_id[:8]}... as {email}")
        return visitor

    def _process_identification_token(self, visitor: WebsiteVisitor, token: str):
        """Process an email identification token.

        This token is typically added to links in email campaigns to identify
        the visitor when they click through.

        Args:
            visitor: WebsiteVisitor instance
            token: Identification token
        """
        # Token format: contact_id or encoded email
        # Implementation depends on how you generate these tokens
        try:
            from apps.contacts.models import Contact

            # Try to find contact by token (could be contact ID or hashed email)
            # For security, use a signed token in production
            contact = Contact.objects.filter(id=token).first()
            if contact:
                visitor.contact = contact
                visitor.is_identified = True
                visitor.identified_at = timezone.now()
                visitor.identification_method = 'email_link'
                visitor.save(update_fields=[
                    'contact', 'is_identified', 'identified_at',
                    'identification_method', 'updated_at'
                ])

                VisitorIdentification.objects.create(
                    visitor=visitor,
                    contact=contact,
                    method=VisitorIdentification.Method.EMAIL_LINK,
                    email=contact.email,
                    source='email_campaign',
                )

                logger.info(f"Identified visitor via email link: {contact.email}")
        except Exception as e:
            logger.error(f"Error processing identification token: {e}")

    # ==================== IP Matching ====================

    def match_visitor_to_contact_by_ip(
        self,
        visitor: WebsiteVisitor
    ) -> Optional['Contact']:
        """Try to match a visitor to an existing contact by IP address.

        This looks for other visitors from the same IP who have been identified,
        suggesting they might be the same person.

        Args:
            visitor: WebsiteVisitor instance

        Returns:
            Contact if matched, None otherwise
        """
        if not visitor.ip_address or visitor.is_identified:
            return None

        # Look for other identified visitors from same IP
        identified_visitor = WebsiteVisitor.objects.filter(
            workspace=visitor.workspace,
            ip_address=visitor.ip_address,
            is_identified=True,
            contact__isnull=False,
        ).exclude(id=visitor.id).order_by('-identified_at').first()

        if identified_visitor:
            contact = identified_visitor.contact

            # Update visitor
            visitor.contact = contact
            visitor.is_identified = True
            visitor.identified_at = timezone.now()
            visitor.identification_method = 'ip_match'
            visitor.save(update_fields=[
                'contact', 'is_identified', 'identified_at',
                'identification_method', 'updated_at'
            ])

            VisitorIdentification.objects.create(
                visitor=visitor,
                contact=contact,
                method=VisitorIdentification.Method.IP_MATCH,
                email=contact.email,
                source='ip_address_match',
                metadata={'matched_visitor_id': str(identified_visitor.id)},
            )

            logger.info(f"Matched visitor {visitor.visitor_id[:8]}... to {contact.email} via IP")
            return contact

        return None

    # ==================== Session Management ====================

    def end_session(self, session_id: str, duration_seconds: int = 0, max_scroll_depth: int = 0):
        """End a visitor session.

        Args:
            session_id: Session ID
            duration_seconds: Total session duration
            max_scroll_depth: Maximum scroll depth achieved
        """
        try:
            session = VisitorSession.objects.get(session_id=session_id)
            session.is_active = False
            session.ended_at = timezone.now()
            session.duration_seconds = duration_seconds
            session.max_scroll_depth = max_scroll_depth
            session.save(update_fields=[
                'is_active', 'ended_at', 'duration_seconds',
                'max_scroll_depth', 'updated_at'
            ])

            # Update visitor total time
            visitor = session.visitor
            visitor.total_time_on_site += duration_seconds
            visitor.save(update_fields=['total_time_on_site', 'updated_at'])

            logger.debug(f"Ended session {session_id[:8]}...")
        except VisitorSession.DoesNotExist:
            logger.warning(f"Session not found: {session_id}")

    def update_page_metrics(
        self,
        visitor_id: str,
        session_id: str,
        page_path: str,
        time_on_page: int = 0,
        scroll_depth: int = 0,
    ):
        """Update metrics for a page view.

        Args:
            visitor_id: Visitor ID
            session_id: Session ID
            page_path: Page path
            time_on_page: Time spent on page in seconds
            scroll_depth: Maximum scroll depth (0-100)
        """
        try:
            page_view = PageView.objects.filter(
                visitor__visitor_id=visitor_id,
                session__session_id=session_id,
                page_path=page_path,
            ).order_by('-created_at').first()

            if page_view:
                page_view.time_on_page = time_on_page
                page_view.scroll_depth = scroll_depth
                page_view.save(update_fields=['time_on_page', 'scroll_depth', 'updated_at'])
        except Exception as e:
            logger.error(f"Error updating page metrics: {e}")

    # ==================== Scoring ====================

    def _award_score(self, contact, points: int, event_type: str, source_object):
        """Award score to contact for website activity.

        Args:
            contact: Contact instance
            points: Points to award
            event_type: Type of event
            source_object: Source object for metadata
        """
        try:
            from apps.contacts.services.scoring_engine import ScoringEngine
            engine = ScoringEngine(contact.workspace)
            engine.apply_event(contact, event_type, metadata={
                'source': 'website_tracking',
                'source_id': str(source_object.id) if source_object else None,
                'points': points,
            })
        except Exception as e:
            logger.error(f"Error awarding score for {event_type}: {e}")

    # ==================== Helpers ====================

    def _parse_user_agent(self, user_agent: str) -> dict:
        """Parse user agent for device information.

        Args:
            user_agent: User agent string

        Returns:
            Dict with device info
        """
        if not user_agent:
            return {}

        result = {
            'device_type': 'desktop',
            'browser_name': '',
            'browser_version': '',
            'os_name': '',
            'os_version': '',
        }

        import re
        ua_lower = user_agent.lower()

        # Device type
        if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
            result['device_type'] = 'mobile'
        elif 'tablet' in ua_lower or 'ipad' in ua_lower:
            result['device_type'] = 'tablet'

        # Browser
        browser_patterns = [
            (r'Edg[eA]?/(\d+[\.\d]*)', 'Edge'),
            (r'Chrome/(\d+[\.\d]*)', 'Chrome'),
            (r'Safari/(\d+[\.\d]*)', 'Safari'),
            (r'Firefox/(\d+[\.\d]*)', 'Firefox'),
        ]
        for pattern, name in browser_patterns:
            match = re.search(pattern, user_agent, re.IGNORECASE)
            if match:
                result['browser_name'] = name
                result['browser_version'] = match.group(1)
                break

        # OS
        os_patterns = [
            (r'Windows NT (\d+[\.\d]*)', 'Windows'),
            (r'Mac OS X (\d+[_\.\d]*)', 'macOS'),
            (r'iPhone OS (\d+[_\.\d]*)', 'iOS'),
            (r'Android (\d+[\.\d]*)', 'Android'),
            (r'Linux', 'Linux'),
        ]
        for pattern, name in os_patterns:
            match = re.search(pattern, user_agent, re.IGNORECASE)
            if match:
                result['os_name'] = name
                if match.lastindex:
                    result['os_version'] = match.group(1).replace('_', '.')
                break

        return result

    def generate_identification_token(self, contact) -> str:
        """Generate a secure identification token for email links.

        Args:
            contact: Contact instance

        Returns:
            Identification token
        """
        # In production, use a signed token for security
        # For now, use a simple approach
        import hashlib
        token_data = f"{contact.id}:{contact.email}:{secrets.token_hex(8)}"
        return hashlib.sha256(token_data.encode()).hexdigest()[:32]
