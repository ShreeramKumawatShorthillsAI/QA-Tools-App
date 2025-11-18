"""Validation and formatting rules for JSON models."""
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .config import Config


class TextFormatter:
    """Handles text formatting operations."""
    
    @staticmethod
    def capitalize_words(text: str) -> str:
        """Capitalize first letter of each word if not already capitalized."""
        if not text or not isinstance(text, str):
            return text
        
        words = text.strip().split(" ")
        result = []
        
        for word in words:
            if word and word[0].islower():
                word = word[0].upper() + word[1:]
            result.append(word)
        
        return " ".join(result)
    
    @staticmethod
    def normalize_units(text: str) -> str:
        """Normalize unit abbreviations."""
        if not text or not isinstance(text, str):
            return text
        
        for old, new in Config.UNIT_REPLACEMENTS.items():
            text = text.replace(old, new)
        
        return text
    
    @staticmethod
    def camel_case(text: str) -> str:
        """Convert text to camelCase."""
        if not text or not isinstance(text, str):
            return text
        
        parts = text.split(" ")
        parts = [x.title() for x in parts]
        parts[0] = parts[0].lower()
        result = "".join(parts)
        
        # Remove special characters
        result = re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "", result)
        result = re.sub('[^A-Za-z0-9]+', '', result)
        
        return result


class URLValidator:
    """Validates URLs."""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is properly formatted."""
        if not url or not isinstance(url, str):
            return False
        
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False


class ListCleaner:
    """Cleans lists by removing empty elements."""
    
    @staticmethod
    def clean_empty_elements(lst: List) -> Optional[List]:
        """Remove empty elements from a list."""
        if not isinstance(lst, list):
            return lst
        
        cleaned = [item for item in lst if item and str(item).strip()]
        return cleaned if cleaned else None


class GeneralSectionValidator:
    """Validates and formats the general section of a model."""
    
    def __init__(self, text_formatter: TextFormatter):
        self.text_formatter = text_formatter
    
    def validate_and_format(
        self, 
        general: Dict[str, Any], 
        file_name: str, 
        model_name: str,
        formatted_names_cache: Dict[str, str]
    ) -> tuple[Dict[str, Any], List[str]]:
        """Validate and format general section."""
        issues = []
        
        if not general or not isinstance(general, dict):
            issues.append(f"Missing or invalid 'general' section in {file_name} - {model_name}")
            return general, issues
        
        # Ensure required fields exist
        for field in Config.REQUIRED_GENERAL_FIELDS:
            if field not in general:
                issues.append(f"Missing required field '{field}' in general section - {file_name} - {model_name}")
                general[field] = None if field != "msrp" else 0
        
        # Format text fields
        issues.extend(self._format_text_fields(general, file_name, model_name, formatted_names_cache))
        
        # Validate year
        issues.extend(self._validate_year(general, file_name, model_name))
        
        # Validate MSRP
        issues.extend(self._validate_msrp(general, file_name, model_name))
        
        # Validate countries
        issues.extend(self._validate_countries(general, file_name, model_name))
        
        return general, issues
    
    def _format_text_fields(
        self, 
        general: Dict, 
        file_name: str, 
        model_name: str,
        formatted_names_cache: Dict[str, str]
    ) -> List[str]:
        """Format manufacturer, model, category, subcategory."""
        issues = []
        
        # Manufacturer, category, subcategory - simple capitalization
        for field in ["manufacturer", "category", "subcategory"]:
            if general.get(field):
                old_val = general[field]
                general[field] = self.text_formatter.capitalize_words(str(general[field]))
                if old_val != general[field]:
                    issues.append(f"Formatted {field}: '{old_val}' → '{general[field]}' in {file_name} - {model_name}")
        
        # Model - use cached formatted name from Gemini
        if general.get("model"):
            old_val = general["model"]
            general["model"] = formatted_names_cache.get(str(general["model"]), str(general["model"]))
            if old_val != general["model"]:
                issues.append(f"Formatted model: '{old_val}' → '{general['model']}' in {file_name} - {model_name}")
        
        return issues
    
    def _validate_year(self, general: Dict, file_name: str, model_name: str) -> List[str]:
        """Validate and convert year to integer."""
        issues = []
        
        if general.get("year"):
            try:
                if not isinstance(general["year"], int):
                    old_val = general["year"]
                    general["year"] = int(general["year"])
                    issues.append(f"Converted year to integer: {old_val} → {general['year']} in {file_name} - {model_name}")
            except (ValueError, TypeError):
                issues.append(f"Invalid year value '{general['year']}' in {file_name} - {model_name}, setting to None")
                general["year"] = None
        
        return issues
    
    def _validate_msrp(self, general: Dict, file_name: str, model_name: str) -> List[str]:
        """Validate and convert MSRP to number."""
        issues = []
        
        if "msrp" in general:
            try:
                msrp_val = general["msrp"]
                
                if isinstance(msrp_val, str):
                    msrp_val = msrp_val.replace(',', '').strip()
                    if msrp_val:
                        msrp_float = float(msrp_val)
                        general["msrp"] = int(msrp_float) if msrp_float.is_integer() else msrp_float
                        issues.append(f"Formatted MSRP: {general['msrp']} in {file_name} - {model_name}")
                    else:
                        general["msrp"] = 0
                elif msrp_val is None:
                    general["msrp"] = 0
                    
            except (ValueError, TypeError):
                issues.append(f"Invalid MSRP value '{general.get('msrp')}' in {file_name} - {model_name}, setting to 0")
                general["msrp"] = 0
        
        return issues
    
    def _validate_countries(self, general: Dict, file_name: str, model_name: str) -> List[str]:
        """Validate countries field."""
        issues = []
        
        if "countries" in general:
            if general["countries"] and isinstance(general["countries"], list):
                original = general["countries"].copy()
                filtered = [c for c in general["countries"] if c in Config.VALID_COUNTRIES]
                
                if not filtered:
                    general["countries"] = Config.VALID_COUNTRIES.copy()
                    issues.append(f"No valid countries found, set to default {Config.VALID_COUNTRIES} in {file_name} - {model_name}")
                elif filtered != original:
                    general["countries"] = filtered
                    removed = [c for c in original if c not in filtered]
                    issues.append(f"Removed invalid countries {removed} in {file_name} - {model_name}")
            else:
                general["countries"] = Config.VALID_COUNTRIES.copy()
                issues.append(f"Empty or invalid countries, set to default {Config.VALID_COUNTRIES} in {file_name} - {model_name}")
        else:
            general["countries"] = Config.VALID_COUNTRIES.copy()
            issues.append(f"Missing countries field, set to default {Config.VALID_COUNTRIES} in {file_name} - {model_name}")
        
        return issues


class MediaValidator:
    """Validates media URLs (images, videos, attachments)."""
    
    def __init__(self, url_validator: URLValidator):
        self.url_validator = url_validator
    
    def validate_images(self, model: Dict, file_name: str, model_name: str) -> List[str]:
        """Validate and clean images."""
        issues = []
        
        if "images" not in model or not model["images"]:
            return issues
        
        if not isinstance(model["images"], list):
            return issues
        
        valid_images = []
        for idx, img in enumerate(model["images"]):
            if isinstance(img, dict) and "src" in img:
                if self.url_validator.is_valid_url(img["src"]):
                    if "desc" not in img:
                        img["desc"] = ""
                    if "longDesc" not in img:
                        img["longDesc"] = ""
                    valid_images.append(img)
                else:
                    issues.append(f"Invalid image URL removed at index {idx} in {file_name} - {model_name}")
            elif isinstance(img, str):
                if self.url_validator.is_valid_url(img):
                    valid_images.append({"src": img, "desc": "", "longDesc": ""})
                else:
                    issues.append(f"Invalid image URL string removed at index {idx} in {file_name} - {model_name}")
        
        model["images"] = valid_images if valid_images else None
        return issues
    
    def validate_videos(self, model: Dict, file_name: str, model_name: str) -> List[str]:
        """Validate and clean videos."""
        issues = []
        
        if "videos" not in model or not model["videos"]:
            return issues
        
        if not isinstance(model["videos"], list):
            return issues
        
        valid_videos = []
        for idx, vid in enumerate(model["videos"]):
            if isinstance(vid, dict):
                url_key = "src" if "src" in vid else ("videoLocation" if "videoLocation" in vid else None)
                
                if url_key and self.url_validator.is_valid_url(vid[url_key]):
                    if url_key == "videoLocation":
                        vid["src"] = vid.pop("videoLocation")
                    if "videoDescription" in vid:
                        vid["desc"] = vid.pop("videoDescription")
                    if "videoName" in vid:
                        vid["longDesc"] = vid.pop("videoName")
                    if "desc" not in vid:
                        vid["desc"] = ""
                    if "longDesc" not in vid:
                        vid["longDesc"] = ""
                    valid_videos.append(vid)
                else:
                    issues.append(f"Invalid video URL removed at index {idx} in {file_name} - {model_name}")
            elif isinstance(vid, str):
                if self.url_validator.is_valid_url(vid):
                    valid_videos.append({"src": vid, "desc": "", "longDesc": ""})
                else:
                    issues.append(f"Invalid video URL string removed at index {idx} in {file_name} - {model_name}")
        
        model["videos"] = valid_videos if valid_videos else None
        return issues
    
    def validate_attachments(self, model: Dict, file_name: str, model_name: str) -> List[str]:
        """Validate and clean attachments."""
        issues = []
        
        if "attachments" not in model or not model["attachments"]:
            return issues
        
        if not isinstance(model["attachments"], list):
            return issues
        
        valid_attachments = []
        pdf_counter = 1
        
        for idx, att in enumerate(model["attachments"]):
            if isinstance(att, dict):
                url_key = "attachmentLocation" if "attachmentLocation" in att else ("src" if "src" in att else None)
                
                if url_key and att.get(url_key) and self.url_validator.is_valid_url(att[url_key]):
                    if url_key == "src":
                        att["attachmentLocation"] = att.pop("src")
                    if "attachmentDescription" not in att or not att["attachmentDescription"]:
                        att["attachmentDescription"] = f"pdf {pdf_counter}"
                    if "attachmentName" not in att:
                        att["attachmentName"] = ""
                    valid_attachments.append(att)
                    pdf_counter += 1
                else:
                    issues.append(f"Invalid or empty attachment URL removed at index {idx} in {file_name} - {model_name}")
            elif isinstance(att, str):
                if att and self.url_validator.is_valid_url(att):
                    valid_attachments.append({
                        "attachmentLocation": att,
                        "attachmentDescription": f"pdf {pdf_counter}",
                        "attachmentName": ""
                    })
                    pdf_counter += 1
                else:
                    issues.append(f"Invalid or empty attachment URL string removed at index {idx} in {file_name} - {model_name}")
        
        model["attachments"] = valid_attachments if valid_attachments else None
        return issues

