import re
import logging
from typing import List, Dict
from .token_store import TokenStore

logger = logging.getLogger(__name__)

class TextEngine:
    """
    Handles safe string substitution for forward redaction and reverse restoration.
    """
    
    @staticmethod
    def redact(text: str, entities: List[Dict[str, str]]) -> str:
        """
        Replaces identified entities with their tokens in the text.
        Handles duplicates natively by replacing all occurrences.
        Sorts entities by length (descending) to avoid partial replacement of overlapping entities.
        """
        if not text or not entities:
            return text
            
        redacted_text = text
        
        # Sort by length descending to replace "John Smith" before "John"
        sorted_entities = sorted(entities, key=lambda x: len(x.get("text", "")), reverse=True)
        
        # Keep track of replaced tokens to avoid double replacement if a token resembles an entity
        for entity in sorted_entities:
            entity_text = entity.get("text")
            token = entity.get("token")
            
            if not entity_text or not token:
                continue
                
            # Use regex with word boundaries if the entity starts/ends with alphanumeric characters
            # Otherwise, just use string replacement (for entities with special chars)
            escaped_text = re.escape(entity_text)
            
            if entity_text[0].isalnum() and entity_text[-1].isalnum():
                pattern = r'\b' + escaped_text + r'\b'
                try:
                    redacted_text = re.sub(pattern, token, redacted_text)
                except re.error as e:
                    logger.error(f"Regex error for {entity_text}: {e}")
                    redacted_text = redacted_text.replace(entity_text, token)
            else:
                redacted_text = redacted_text.replace(entity_text, token)
                
        return redacted_text

    @staticmethod
    def restore(session_id: str, redacted_text: str, token_store: TokenStore) -> str:
        """
        Reconstructs the original text by finding all tokens and replacing them with original values.
        """
        if not redacted_text:
            return redacted_text
            
        restored_text = redacted_text
        
        # Find all potential tokens in the text (e.g., PATIENT_001, DOCTOR_001)
        # Matches uppercase letters followed by underscore and digits
        token_pattern = r'\b[A-Z]+_\d+\b'
        found_tokens = list(set(re.findall(token_pattern, redacted_text)))
        
        # Sort tokens by length descending, just in case (though format is standard)
        found_tokens.sort(key=len, reverse=True)
        
        for token in found_tokens:
            original_value = token_store.get_name_from_token(session_id, token)
            if original_value:
                # Replace all occurrences of the token
                restored_text = re.sub(r'\b' + re.escape(token) + r'\b', original_value, restored_text)
            else:
                logger.warning(f"Could not restore token {token} in session {session_id}")
                
        return restored_text
