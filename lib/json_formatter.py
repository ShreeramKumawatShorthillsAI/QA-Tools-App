"""Main JSON formatter class with OOP architecture."""
from typing import Any, Dict, List, Optional

from .config import Config
from .validators import (
    TextFormatter, URLValidator, ListCleaner,
    GeneralSectionValidator, MediaValidator
)
from .gemini_client import GeminiAPIClient


class ModelReport:
    """Manages formatting report."""
    
    def __init__(self):
        self.total_models = 0
        self.processed_models = 0
        self.failed_models = 0
        self.issues_by_model: Dict[str, List[str]] = {}
        self.errors: List[str] = []
    
    def add_issue(self, model_name: str, issue: str) -> None:
        """Add an issue for a specific model."""
        if model_name not in self.issues_by_model:
            self.issues_by_model[model_name] = []
        self.issues_by_model[model_name].append(issue)
    
    def add_error(self, error: str) -> None:
        """Add a general error."""
        self.errors.append(error)
    
    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        return {
            "total_models": self.total_models,
            "processed_models": self.processed_models,
            "failed_models": self.failed_models,
            "issues_by_model": self.issues_by_model,
            "errors": self.errors
        }


class JSONModelFormatter:
    """Main formatter for JSON models."""
    
    def __init__(self, gemini_client: GeminiAPIClient):
        """
        Initialize JSON formatter.
        
        Args:
            gemini_client: Client for Gemini API calls
        """
        self.gemini_client = gemini_client
        self.report = ModelReport()
        self.formatted_names_cache: Dict[str, str] = {}
        
        # Initialize validators
        self.text_formatter = TextFormatter()
        self.url_validator = URLValidator()
        self.list_cleaner = ListCleaner()
        self.general_validator = GeneralSectionValidator(self.text_formatter)
        self.media_validator = MediaValidator(self.url_validator)
    
    def prebatch_model_names(self, all_json_data: list, progress_callback=None) -> None:
        """
        Pre-process all model names from all files in batches using Gemini API.
        
        Args:
            all_json_data: List of tuples (json_data, file_name)
            progress_callback: Optional callback function for progress updates
        """
        # Collect ALL model names from ALL files first
        all_model_names = []
        
        for json_data, _ in all_json_data:
            model_names = self._extract_model_names(json_data)
            all_model_names.extend(model_names)
        
        if not all_model_names:
            return
        
        # Remove duplicates while preserving order (optional - for efficiency)
        seen = set()
        unique_model_names = []
        for name in all_model_names:
            if name not in seen:
                seen.add(name)
                unique_model_names.append(name)
        
        # Now process ALL model names in batches of BATCH_SIZE
        total_batches = (len(unique_model_names) + Config.BATCH_SIZE - 1) // Config.BATCH_SIZE
        
        print(f"\n{'='*70}")
        print(f"🚀 STARTING BATCH PROCESSING")
        print(f"{'='*70}")
        print(f"📊 Total unique model names: {len(unique_model_names)}")
        print(f"📦 Total batches: {total_batches}")
        print(f"⏱️  Estimated time: {total_batches * 3} seconds (~3 seconds per batch)")
        print(f"{'='*70}\n")
        
        for i in range(0, len(unique_model_names), Config.BATCH_SIZE):
            batch = unique_model_names[i:i + Config.BATCH_SIZE]
            batch_num = (i // Config.BATCH_SIZE) + 1
            
            print(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} model names)...")
            
            if progress_callback:
                progress_callback(batch_num, total_batches)
            
            formatted_batch = self.gemini_client.capitalize_model_names_batch(batch)
            self.formatted_names_cache.update(formatted_batch)
            
            print(f"✅ Batch {batch_num}/{total_batches} complete!\n")
        
        print(f"{'='*70}")
        print(f"✅ PROCESSING COMPLETE!")
        print(f"📊 Pre-processed {len(unique_model_names)} unique model names in {total_batches} batch(es)")
        print(f"{'='*70}\n")
    
    def _extract_model_names(self, json_data: Any) -> List[str]:
        """Extract all model names from JSON data."""
        model_names = []
        
        if isinstance(json_data, list):
            for model in json_data:
                if isinstance(model, dict) and "general" in model and "model" in model["general"]:
                    name = model["general"]["model"]
                    if name and isinstance(name, str):
                        model_names.append(name)
        else:
            if isinstance(json_data, dict) and "general" in json_data and "model" in json_data["general"]:
                name = json_data["general"]["model"]
                if name and isinstance(name, str):
                    model_names.append(name)
        
        return model_names
    
    def process_json_data(self, json_data: Any, file_name: str = "unknown") -> List[Dict]:
        """
        Process JSON data (list or single object).
        
        Args:
            json_data: JSON data to process
            file_name: Name of source file
            
        Returns:
            List of formatted models
        """
        if isinstance(json_data, list):
            self.report.total_models += len(json_data)
            formatted_models = []
            
            for model in json_data:
                formatted_model, success = self._format_single_model(model, file_name)
                if success:
                    formatted_models.append(formatted_model)
            
            return formatted_models
        else:
            self.report.total_models += 1
            formatted_model, success = self._format_single_model(json_data, file_name)
            return [formatted_model] if success else []
    
    def _format_single_model(self, model: Dict, file_name: str) -> tuple[Dict, bool]:
        """Format a single model."""
        try:
            model_name = self._get_model_name(model)
            
            # Format general section
            if "general" in model:
                model["general"], issues = self.general_validator.validate_and_format(
                    model["general"], 
                    file_name, 
                    model_name,
                    self.formatted_names_cache
                )
                for issue in issues:
                    self.report.add_issue(model_name, issue)
                
                # Update model name after formatting
                model_name = self._get_model_name(model)
            else:
                self.report.add_issue(model_name, f"Missing 'general' section in {file_name}")
            
            # Format media
            issues = []
            issues.extend(self.media_validator.validate_images(model, file_name, model_name))
            issues.extend(self.media_validator.validate_videos(model, file_name, model_name))
            issues.extend(self.media_validator.validate_attachments(model, file_name, model_name))
            
            for issue in issues:
                self.report.add_issue(model_name, issue)
            
            # Clean lists
            issues = self._clean_lists(model, file_name, model_name)
            for issue in issues:
                self.report.add_issue(model_name, issue)
            
            # Format specifications
            issues = self._format_specifications(model, file_name, model_name)
            for issue in issues:
                self.report.add_issue(model_name, issue)
            
            # Remove null fields
            model = self._remove_null_fields(model)
            
            self.report.processed_models += 1
            return model, True
            
        except Exception as e:
            error_msg = f"Error processing model in {file_name} - {model_name}: {str(e)}"
            self.report.add_error(error_msg)
            self.report.failed_models += 1
            return model, False
    
    def _get_model_name(self, model: Dict) -> str:
        """Extract model name from model object."""
        try:
            if isinstance(model, dict) and "general" in model and "model" in model["general"]:
                return model["general"]["model"]
        except:
            pass
        return "Unknown Model"
    
    def _clean_lists(self, model: Dict, file_name: str, model_name: str) -> List[str]:
        """Clean features and options lists."""
        issues = []
        
        for field in ["features", "options"]:
            if field in model and model[field]:
                original_count = len(model[field]) if isinstance(model[field], list) else 0
                model[field] = self.list_cleaner.clean_empty_elements(model[field])
                new_count = len(model[field]) if model[field] else 0
                
                if original_count != new_count:
                    issues.append(f"Removed {original_count - new_count} empty {field[:-1]}(s) in {file_name} - {model_name}")
        
        return issues
    
    def _format_specifications(self, model: Dict, file_name: str, model_name: str) -> List[str]:
        """Format specification sections."""
        issues = []
        
        for section in Config.SPEC_SECTIONS:
            if section not in model or not model[section]:
                continue
            
            if not isinstance(model[section], dict):
                continue
            
            formatted_section = {}
            for key, value in model[section].items():
                if isinstance(value, dict) and "label" in value and "desc" in value:
                    if value["desc"]:
                        old_desc = value["desc"]
                        value["desc"] = self.text_formatter.normalize_units(str(value["desc"]))
                        
                        if old_desc != value["desc"]:
                            issues.append(f"Normalized units in {section}.{key} in {file_name} - {model_name}")
                    
                    proper_key = self.text_formatter.camel_case(key)
                    formatted_section[proper_key] = value
                else:
                    formatted_section[key] = value
            
            model[section] = formatted_section if formatted_section else None
        
        return issues
    
    def _remove_null_fields(self, model: Dict) -> Dict:
        """Remove null/None fields from model."""
        def clean_dict(d, parent_key=None):
            if isinstance(d, dict):
                cleaned = {}
                for k, v in d.items():
                    # Keep empty strings for specific media fields
                    if k in Config.MEDIA_EMPTY_FIELDS and v == "":
                        cleaned[k] = v
                    # Remove null, empty strings, and empty arrays
                    elif v is not None and v != [] and not (v == "" and k not in Config.MEDIA_EMPTY_FIELDS):
                        cleaned[k] = clean_dict(v, k)
                return cleaned
            elif isinstance(d, list):
                cleaned = [clean_dict(v) for v in d if v is not None and v != "" and v != []]
                return cleaned if cleaned else None
            else:
                return d
        
        return clean_dict(model)

