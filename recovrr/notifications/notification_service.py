"""Main notification service that coordinates different notification methods."""

import logging
from typing import Dict, Any, List, Optional

from recovrr.config.settings import settings
from .base_notifier import BaseNotifier
from .email_notifier import EmailNotifier
from .sms_notifier import SMSNotifier

logger = logging.getLogger(__name__)


class NotificationService:
    """Service that manages and coordinates different notification methods."""
    
    def __init__(self):
        """Initialize notification service with available notifiers."""
        self.notifiers: Dict[str, BaseNotifier] = {}
        self._setup_notifiers()
        
    def _setup_notifiers(self):
        """Set up available notification services based on configuration."""
        # Set up email notifier if configured
        if settings.sendgrid_api_key:
            try:
                self.notifiers['email'] = EmailNotifier()
                logger.info("Email notifier configured successfully")
            except Exception as e:
                logger.error(f"Failed to configure email notifier: {e}")
                
        # Set up SMS notifier if configured
        if all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_phone_number]):
            try:
                self.notifiers['sms'] = SMSNotifier()
                logger.info("SMS notifier configured successfully")
            except Exception as e:
                logger.error(f"Failed to configure SMS notifier: {e}")
                
        if not self.notifiers:
            logger.warning("No notification services configured!")
            
    async def send_match_alert(
        self,
        search_profile: dict[str, Any],
        listing: dict[str, Any],
        analysis_result: dict[str, Any]
    ) -> Dict[str, bool]:
        """Send match alerts through all configured notification methods.
        
        Args:
            search_profile: Search profile that matched
            listing: Marketplace listing information
            analysis_result: AI analysis results
            
        Returns:
            Dictionary mapping notification method to success status
        """
        results = {}
        
        # Get recipient information from search profile
        email = search_profile.get('owner_email')
        phone = search_profile.get('owner_phone')
        
        # Send email notification
        if 'email' in self.notifiers and email:
            try:
                success = await self.notifiers['email'].send_match_notification(
                    email, search_profile, listing, analysis_result
                )
                results['email'] = success
                logger.info(f"Email notification result: {success}")
            except Exception as e:
                logger.error(f"Error sending email notification: {e}")
                results['email'] = False
                
        # Send SMS notification for high-priority matches
        if ('sms' in self.notifiers and phone and 
            (analysis_result.get('match_score', 0) >= 8 or 
             analysis_result.get('recommendation') == 'high_priority')):
            try:
                success = await self.notifiers['sms'].send_match_notification(
                    phone, search_profile, listing, analysis_result
                )
                results['sms'] = success
                logger.info(f"SMS notification result: {success}")
            except Exception as e:
                logger.error(f"Error sending SMS notification: {e}")
                results['sms'] = False
                
        return results
        
    async def send_system_alert(
        self,
        recipients: list[str],
        subject: str,
        message: str,
        methods: Optional[list[str]] = None
    ) -> Dict[str, Dict[str, bool]]:
        """Send system alerts to specified recipients.
        
        Args:
            recipients: List of recipient identifiers
            subject: Alert subject
            message: Alert message
            methods: Specific notification methods to use (default: all available)
            
        Returns:
            Nested dictionary: {method: {recipient: success}}
        """
        if methods is None:
            methods = list(self.notifiers.keys())
            
        results = {method: {} for method in methods}
        
        for method in methods:
            if method not in self.notifiers:
                logger.warning(f"Notification method '{method}' not available")
                continue
                
            notifier = self.notifiers[method]
            
            for recipient in recipients:
                try:
                    success = await notifier.send_system_notification(
                        recipient, subject, message
                    )
                    results[method][recipient] = success
                except Exception as e:
                    logger.error(f"Error sending {method} to {recipient}: {e}")
                    results[method][recipient] = False
                    
        return results
        
    async def test_notifications(self, test_recipient_email: str, test_recipient_phone: Optional[str] = None) -> Dict[str, bool]:
        """Test all configured notification methods.
        
        Args:
            test_recipient_email: Email address for testing
            test_recipient_phone: Phone number for testing (optional)
            
        Returns:
            Dictionary mapping notification method to test result
        """
        results = {}
        
        test_subject = "Recovrr Notification Test"
        test_message = "This is a test notification from the Recovrr system. If you receive this, notifications are working correctly."
        
        # Test email
        if 'email' in self.notifiers:
            try:
                success = await self.notifiers['email'].send_system_notification(
                    test_recipient_email, test_subject, test_message
                )
                results['email'] = success
            except Exception as e:
                logger.error(f"Email test failed: {e}")
                results['email'] = False
                
        # Test SMS
        if 'sms' in self.notifiers and test_recipient_phone:
            try:
                success = await self.notifiers['sms'].send_system_notification(
                    test_recipient_phone, test_subject, test_message
                )
                results['sms'] = success
            except Exception as e:
                logger.error(f"SMS test failed: {e}")
                results['sms'] = False
                
        return results
        
    def get_available_methods(self) -> list[str]:
        """Get list of available notification methods.
        
        Returns:
            List of available notification method names
        """
        return list(self.notifiers.keys())
        
    def is_configured(self) -> bool:
        """Check if at least one notification method is configured.
        
        Returns:
            True if at least one notifier is available
        """
        return len(self.notifiers) > 0
