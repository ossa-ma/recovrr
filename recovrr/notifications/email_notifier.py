"""Email notification service using SendGrid."""

import logging
from typing import Dict, Any

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from ..config import settings
from .base_notifier import BaseNotifier

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """Email notification service using SendGrid."""
    
    def __init__(self):
        """Initialize email notifier."""
        super().__init__("email")
        
        if not settings.sendgrid_api_key:
            raise ValueError("SendGrid API key not configured")
            
        self.client = SendGridAPIClient(api_key=settings.sendgrid_api_key)
        self.from_email = "noreply@recovrr.com"  # Configure your domain
        
    async def send_match_notification(
        self,
        recipient: str,
        search_profile: Dict[str, Any],
        listing: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> bool:
        """Send email notification about a potential match.
        
        Args:
            recipient: Email address to send to
            search_profile: Search profile that matched
            listing: Marketplace listing information
            analysis_result: AI analysis results
            
        Returns:
            True if email was sent successfully
        """
        try:
            # Format the message
            message_content = self.format_match_message(
                search_profile, listing, analysis_result
            )
            
            # Create email
            message = Mail(
                from_email=self.from_email,
                to_emails=recipient,
                subject=message_content['subject'],
                plain_text_content=message_content['body']
            )
            
            # Add HTML version for better formatting
            html_body = self._create_html_body(
                search_profile, listing, analysis_result, message_content['body']
            )
            message.content.append(
                {"type": "text/html", "value": html_body}
            )
            
            # Send email
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Match notification email sent to {recipient}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
            
    async def send_system_notification(
        self,
        recipient: str,
        subject: str,
        message: str
    ) -> bool:
        """Send system notification email.
        
        Args:
            recipient: Email address
            subject: Email subject
            message: Email message
            
        Returns:
            True if email was sent successfully
        """
        try:
            email = Mail(
                from_email=self.from_email,
                to_emails=recipient,
                subject=f"[Recovrr System] {subject}",
                plain_text_content=message
            )
            
            response = self.client.send(email)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"System notification email sent to {recipient}")
                return True
            else:
                logger.error(f"Failed to send system email: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending system email: {e}")
            return False
            
    def _create_html_body(
        self,
        search_profile: Dict[str, Any],
        listing: Dict[str, Any],
        analysis_result: Dict[str, Any],
        plain_text: str
    ) -> str:
        """Create HTML version of the email body.
        
        Args:
            search_profile: Search profile information
            listing: Listing information
            analysis_result: Analysis results
            plain_text: Plain text version
            
        Returns:
            HTML formatted email body
        """
        match_score = analysis_result.get('match_score', 0)
        confidence = analysis_result.get('confidence_level', 'unknown')
        recommendation = analysis_result.get('recommendation', 'investigate')
        
        # Determine colors based on score and recommendation
        if recommendation == "high_priority" or match_score >= 8:
            header_color = "#dc3545"  # Red
            score_color = "#dc3545"
        elif match_score >= 6:
            header_color = "#fd7e14"  # Orange
            score_color = "#fd7e14"
        else:
            header_color = "#6c757d"  # Gray
            score_color = "#6c757d"
            
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recovrr Match Alert</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    
    <div style="background-color: {header_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
        <h1 style="margin: 0; font-size: 24px;">🔍 Recovrr Match Alert</h1>
        <p style="margin: 10px 0 0 0; font-size: 16px;">Potential match detected for your stolen item</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-left: 1px solid #dee2e6; border-right: 1px solid #dee2e6;">
        
        <div style="background-color: white; padding: 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid {score_color};">
            <h3 style="margin-top: 0; color: {score_color};">AI Analysis Results</h3>
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span><strong>Match Score:</strong></span>
                <span style="color: {score_color}; font-weight: bold; font-size: 18px;">{match_score}/10</span>
            </div>
            <div style="margin-bottom: 5px;"><strong>Confidence:</strong> {confidence.upper()}</div>
            <div><strong>Recommendation:</strong> {recommendation.upper()}</div>
        </div>
        
        <div style="background-color: white; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">Your Stolen Item</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li><strong>Make:</strong> {search_profile.get('make', 'Unknown')}</li>
                <li><strong>Model:</strong> {search_profile.get('model', 'Unknown')}</li>
                <li><strong>Color:</strong> {search_profile.get('color', 'Unknown')}</li>
                <li><strong>Size:</strong> {search_profile.get('size', 'Unknown')}</li>
            </ul>
        </div>
        
        <div style="background-color: white; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">Marketplace Listing</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li><strong>Title:</strong> {listing.get('title', 'No title')}</li>
                <li><strong>Price:</strong> ${listing.get('price', 'Unknown')}</li>
                <li><strong>Location:</strong> {listing.get('location', 'Unknown')}</li>
                <li><strong>Marketplace:</strong> {listing.get('marketplace', 'Unknown').title()}</li>
            </ul>
            <div style="margin-top: 15px;">
                <a href="{listing.get('url', '#')}" 
                   style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold;">
                   View Listing →
                </a>
            </div>
        </div>
        
        <div style="background-color: white; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">AI Reasoning</h3>
            <p style="margin: 0; font-style: italic; color: #6c757d;">
                {analysis_result.get('reasoning', 'No reasoning provided')}
            </p>
        </div>
        
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #856404;">⚠️ Important Next Steps</h3>
            <ol style="margin: 0; color: #856404;">
                <li>Review the listing immediately</li>
                <li>Contact local authorities if this appears to be your item</li>
                <li><strong>Do NOT contact the seller directly</strong> - work with police</li>
            </ol>
        </div>
        
    </div>
    
    <div style="background-color: #6c757d; color: white; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; font-size: 12px;">
        <p style="margin: 0;">This alert was generated by the Recovrr AI monitoring system.</p>
        <p style="margin: 5px 0 0 0;">Report false positives to help improve accuracy.</p>
    </div>
    
</body>
</html>
"""
        return html
