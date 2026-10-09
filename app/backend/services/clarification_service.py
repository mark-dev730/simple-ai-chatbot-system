"""
Clarification service - handles AI requests for user clarification.
Parses clarification requests and formats them for frontend display.
"""
import re
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ClarificationService:
    """Handles AI clarification requests and responses."""
    
    @staticmethod
    def detect_clarification(ai_response: str) -> Optional[Dict[str, Any]]:
        """
        Detect if AI is asking for clarification.
        
        Returns:
            Dictionary with clarification data or None if no clarification needed
        """
        # Look for [CLARIFICATION] tags
        pattern = r'\[CLARIFICATION\](.*?)\[/CLARIFICATION\]'
        match = re.search(pattern, ai_response, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return None
        
        clarification_text = match.group(1).strip()
        
        try:
            # Try to parse as JSON
            clarification_data = json.loads(clarification_text)
            
            # Validate structure
            if 'question' in clarification_data and 'options' in clarification_data:
                return {
                    'type': 'clarification',
                    'question': clarification_data['question'],
                    'options': clarification_data['options'],
                    'has_custom_input': True  # Always allow custom input
                }
        except json.JSONDecodeError:
            logger.error(f"Failed to parse clarification JSON: {clarification_text}")
        
        return None
    
    @staticmethod
    def format_clarification_response(clarification: Dict[str, Any]) -> str:
        """
        Format clarification for user-friendly display.
        
        Args:
            clarification: Clarification data dict
            
        Returns:
            Formatted text for display
        """
        output = [f"**{clarification['question']}**\n"]
        output.append("Please select an option or provide your own answer:\n")
        
        for i, option in enumerate(clarification['options'], 1):
            output.append(f"{i}. {option}")
        
        return "\n".join(output)
    
    @staticmethod
    def remove_clarification_tags(text: str) -> str:
        """Remove [CLARIFICATION] tags from text."""
        return re.sub(
            r'\[CLARIFICATION\].*?\[/CLARIFICATION\]',
            '',
            text,
            flags=re.DOTALL | re.IGNORECASE
        ).strip()


# Global instance
clarification_service = ClarificationService()

