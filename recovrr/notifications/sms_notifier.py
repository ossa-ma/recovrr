"""SMS notification service using Twilio."""

import logging
from typing import Dict, Any

from twilio.rest import Client

from ..config import settings
from .base_notifier import BaseNotifier

logger = logging.getLogger(__name__)


class SMSNotifier(BaseNotifier):
    """SMS notification service using Twilio."""
    
    def __init__(self):
        """Initialize SMS notifier."""
        super().__init__("sms")
        
        if not all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_phone_number]):
            raise ValueError("Twilio credentials not fully configured")
            
        self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        self.from_phone = settings.twilio_phone_number
        
    async def send_match_notification(
        self,
        recipient: str,
        search_profile: Dict[str, Any],
        listing: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> bool:
        """Send SMS notification about a potential match.
        
        Args:
            recipient: Phone number to send to
            search_profile: Search profile that matched
            listing: Marketplace listing information
            analysis_result: AI analysis results
            
        Returns:
            True if SMS was sent successfully
        """
        try:
            # Create short SMS message (160 char limit consideration)
            message_text = self._create_sms_message(
                search_profile, listing, analysis_result
            )
            
            # Send SMS
            message = self.client.messages.create(
                body=message_text,
                from_=self.from_phone,
                to=recipient
            )
            
            if message.sid:
                logger.info(f"Match notification SMS sent to {recipient}: {message.sid}")
                return True
            else:
                logger.error("Failed to send SMS: No message SID returned")
                return False
                
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            return False
            
    async def send_system_notification(
        self,
        recipient: str,
        subject: str,
        message: str
    ) -> bool:
        """Send system notification SMS.
        
        Args:
            recipient: Phone number
            subject: Message subject (included in message body)
            message: SMS message content
            
        Returns:
            True if SMS was sent successfully
        """
        try:
            full_message = f"[Recovrr] {subject}: {message}"
            
            # Truncate if too long (SMS has character limits)
            if len(full_message) > 1600:  # Most carriers support up to 1600 chars
                full_message = full_message[:1597] + "..."
                
            sms = self.client.messages.create(
                body=full_message,
                from_=self.from_phone,
                to=recipient
            )
            
            if sms.sid:
                logger.info(f"System notification SMS sent to {recipient}: {sms.sid}")
                return True
            else:
                logger.error("Failed to send system SMS: No message SID returned")
                return False
                
        except Exception as e:
            logger.error(f"Error sending system SMS: {e}")
            return False
            
    def _create_sms_message(
        self,
        search_profile: Dict[str, Any],
        listing: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> str:
        """Create SMS message for match notification.
        
        Args:
            search_profile: Search profile information
            listing: Listing information
            analysis_result: Analysis results
            
        Returns:
            SMS message text
        """
        match_score = analysis_result.get('match_score', 0)
        recommendation = analysis_result.get('recommendation', 'investigate')
        
        # Create priority indicator
        if recommendation == "high_priority" or match_score >= 8:
            priority = "🚨 HIGH PRIORITY"
        elif match_score >= 6:
            priority = "⚠️ POTENTIAL MATCH"
        else:
            priority = "📍 POSSIBLE MATCH"
            
        # Build concise message
        item_desc = f"{search_profile.get('make', '')} {search_profile.get('model', '')}".strip()
        if not item_desc:
            item_desc = "your item"
            
        message = f"""{priority}
        
{item_desc} found on {listing.get('marketplace', 'marketplace').title()}!

Score: {match_score}/10
Price: ${listing.get('price', 'Unknown')}
Location: {listing.get('location', 'Unknown')}

View: {listing.get('url', 'No URL')}

Contact police if this is your item. Do NOT contact seller directly.

-Recovrr""".strip()
        
        return message
