"""Gemini API client for model name capitalization."""
import json
from typing import List, Dict
from pydantic import BaseModel
from google import genai

from .api_manager import APIKeyManager


class ListResponse(BaseModel):
    """Pydantic model for API response."""
    list_response: List[str]


class GeminiAPIClient:
    """Client for interacting with Gemini API."""
    
    def __init__(self, api_key_manager: APIKeyManager, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini API client.
        
        Args:
            api_key_manager: Manager for API key rotation
            model: Gemini model to use
        """
        self.api_manager = api_key_manager
        self.model = model
        self.prompt_template = self._create_prompt_template()
    
    def _create_prompt_template(self) -> str:
        """Create the prompt template for model name capitalization."""
        return """# 🧠 Product Model Name Case Corrector

## 🎯 System Role
You are a specialist in industrial product data normalization.  
Your job is to convert ONLY general English words into Title Case, while keeping ALL product codes, series names, and technical identifiers COMPLETELY UNCHANGED.

---

## 🧩 Core Rules

**CRITICAL: When in doubt, DO NOT change the capitalization. Only modify obvious general English words.**

For every model name:

1. **LEAVE THESE COMPLETELY UNTOUCHED (no changes at all):**
   - ANY token containing numbers (BG-40, MTT40-6060, DS72, EPJ-60R)
   - ANY token that is entirely uppercase (BG, EPS, DS, ASM, BGS)
   - ANY token with hyphens followed by numbers (BGN-40, EPS-30)
   - Product/series codes (any combination of letters + numbers)
   - Brand names and acronyms
   - Tokens with special symbols (™, ®)
   - ANY technical or specialized term

2. **ONLY convert these into Title Case:**
   - Simple, common English words (like: hydraulic, powered, barrier, dock, zero, series)
   - Words that are clearly descriptive adjectives or nouns
   - Apply Title Case: First letter uppercase + remaining letters lowercase

3. **Handling connected words:**
   - For hyphenated words (e.g., "AIR-POWERED"):
     - Check EACH part separately
     - If both parts are general English words, convert both: "Air-Powered"
     - If any part is a code/number, leave the ENTIRE token unchanged
   
4. **Strict preservation:**
   - Do NOT add, remove, or reorder any characters
   - Maintain all punctuation, parentheses, quotes, hyphens, symbols exactly as given
   - Preserve spacing exactly as in the original

---

## 💡 Output Format
Return ONLY a JSON array containing the corrected model names in the same order as received.

---

## 🧠 Examples

| Input                          | Output                       | Explanation                          |
|-------------------------------|-------------------------------|--------------------------------------|
| Hydraulic Dock Leveler        | Hydraulic Dock Leveler        | All general words, convert to Title  |
| MTT40-6060                    | MTT40-6060                    | Product code, no change              |
| BGN-40                        | BGN-40                        | Has number, no change                |
| AIR-POWERED DOCK LEVELER      | Air-Powered Dock Leveler      | All general words, convert to Title  |
| DOCK-LIP BARRIER - DLB        | Dock-Lip Barrier - DLB        | "DLB" is uppercase acronym, keep it  |
| DS4-72(DS72 SERIES )          | DS4-72(DS72 Series )          | Keep codes, only "SERIES" → "Series" |
| BG ZERO                       | BG Zero                       | "BG" is uppercase, keep; "ZERO" → "Zero" |
| EPS-30                        | EPS-30                        | Has number, no change                |
| ASM SERIES                    | ASM Series                    | "ASM" is uppercase, keep; "SERIES" → "Series" |
| BG 40                         | BG 40                         | Has number, no change                |
| BGS-32                        | BGS-32                        | Has number, no change                |
| MOBILE DOCK LEVELER           | Mobile Dock Leveler           | All general words, convert to Title  |

---

## 📋 Model Names to Correct
{model_names_list}
"""
    
    def capitalize_model_names_batch(self, model_names: List[str]) -> Dict[str, str]:
        """
        Capitalize multiple model names in a single API call.
        
        Args:
            model_names: List of model names to capitalize
            
        Returns:
            Dictionary mapping original names to formatted names
        """
        if not model_names:
            return {}
        
        # Create numbered list
        numbered_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(model_names)])
        prompt = self.prompt_template.format(model_names_list=numbered_list)
        
        # Try with current key, fallback to all keys if needed
        tried_keys = set()
        max_retries = len(self.api_manager.api_keys)
        
        for retry in range(max_retries):
            current_key = self.api_manager.get_current_key()
            current_key_num = self.api_manager.get_current_key_number()
            
            # Skip if already tried
            if current_key in tried_keys:
                self.api_manager.rotate_on_failure()
                continue
            
            tried_keys.add(current_key)
            
            try:
                print(f"   📡 Making API call (Using key #{current_key_num})...")
                result = self._make_api_call(current_key, prompt)
                
                if result and len(result) == len(model_names):
                    # Success! Create mapping
                    mapping = {model_names[i]: result[i] for i in range(len(model_names))}
                    self.api_manager.increment_call_count()
                    
                    # Get updated status after increment
                    status = self.api_manager.get_status()
                    print(f"   ✅ API call successful! (Key #{current_key_num}: {status['calls_with_current_key']}/{status['max_calls_per_key']} calls used)")
                    
                    return mapping
                
            except Exception as e:
                self._handle_api_error(e)
                self.api_manager.rotate_on_failure()
                continue
        
        # All keys failed - return original names
        print(f"   ⚠️  All API keys exhausted. Using original names for this batch.")
        return {name: name for name in model_names}
    
    def _make_api_call(self, api_key: str, prompt: str) -> List[str]:
        """Make API call to Gemini."""
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ListResponse
            },
        )
        
        response_data = response.text
        response_json = json.loads(response_data)
        return response_json.get("list_response", [])
    
    def _handle_api_error(self, error: Exception) -> None:
        """Handle and log API errors."""
        key_num = self.api_manager.get_current_key_number()
        error_str = str(error)
        
        if "Resource has been exhausted" in error_str or "quota" in error_str.lower():
            print(f"   ❌ API key #{key_num}: Quota exhausted, rotating to next key...")
        elif "429" in error_str:
            print(f"   ❌ API key #{key_num}: Rate limit reached, rotating to next key...")
        else:
            print(f"   ❌ API key #{key_num}: Error occurred, rotating to next key...")

