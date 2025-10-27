import streamlit as st
import json
import zipfile
import tarfile
import io
import re
from datetime import datetime
from urllib.parse import urlparse
import requests

# Set page configuration
st.set_page_config(page_title="JSON Formatter & Validator", layout="wide")

# Header
st.header("JSON Formatter & Validator Tool")
st.markdown("""
🔧 This tool formats and validates JSON model files according to standard rules.

---

### 📝 Instructions
1. **Upload**: Single JSON file(s), multiple JSON files, or a compressed archive (`.zip`, `.tar`, `.tar.gz`)
2. **Process**: The tool will format and validate each model according to the rules.
3. **Download**: Get the cleaned JSON file and a detailed report.

---
""")


class JSONFormatter:
    """Class to format and validate JSON models."""
    
    def __init__(self):
        self.report = {
            "total_models": 0,
            "processed_models": 0,
            "failed_models": 0,
            "issues_by_model": {},  # Changed to dict to group by model
            "errors": []
        }
        
    def capitalize_words(self, text):
        """Capitalize first letter of each word if not already capitalized."""
        if not text or not isinstance(text, str):
            return text
            
        words = text.strip().split(" ")
        result = []
        
        for word in words:
            if word:
                # Only capitalize first letter if it's not already capital
                if word[0].islower():
                    word = word[0].upper() + word[1:]
                result.append(word)
                
        return " ".join(result)
    
    def validate_url(self, url):
        """Validate if URL is properly formatted."""
        if not url or not isinstance(url, str):
            return False
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def clean_empty_elements(self, lst):
        """Remove empty elements from a list."""
        if not isinstance(lst, list):
            return lst
        cleaned = [item for item in lst if item and str(item).strip()]
        return cleaned if cleaned else None
    
    def normalize_units(self, text):
        """Normalize unit abbreviations."""
        if not text or not isinstance(text, str):
            return text
            
        replacements = {
            "in.": "in", "ft.": "ft", "FT.": "FT", "Ft.": "Ft", "yd.": "yd",
            "mi.": "mi", "cm.": "cm", "mm.": "mm", "m.": "m",
            "max.": "max", "Max.": "Max", "min.": "min", "Min.": "Min",
            "avg.": "avg", "Avg.": "Avg", "nom.": "nom", "Nom.": "Nom",
            "lbs.": "lbs", "lb.": "lb", "oz.": "oz",
            "cu.": "cu", "gal.": "gal", "qt.": "qt", "pt.": "pt",
            "sec.": "sec", "Sec.": "Sec", "hr.": "hr", "hrs.": "hr",
            "°F.": "°F", "°C.": "°C"
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    def camel_case(self, text):
        """Convert text to camelCase."""
        if not text or not isinstance(text, str):
            return text
        s = text.split(" ")
        s = [x.title() for x in s]
        s[0] = s[0].lower()
        s = "".join(s)
        s = re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "", s)
        s = re.sub('[^A-Za-z0-9]+', '', s)
        return s
    
    def get_model_name(self, model):
        """Extract model name from model object."""
        try:
            if isinstance(model, dict) and "general" in model and "model" in model["general"]:
                return model["general"]["model"]
        except:
            pass
        return "Unknown Model"
    
    def format_general_section(self, general, file_name, model_name):
        """Format and validate the general section."""
        issues = []
        
        if not general or not isinstance(general, dict):
            issues.append(f"Missing or invalid 'general' section in {file_name} - {model_name}")
            return general, issues
        
        # Required fields
        required_fields = ["manufacturer", "model", "year", "msrp", "category", "subcategory", "description", "countries"]
        for field in required_fields:
            if field not in general:
                issues.append(f"Missing required field '{field}' in general section - {file_name} - {model_name}")
                general[field] = None if field != "msrp" else 0
        
        # Capitalize manufacturer, model, category, subcategory
        if general.get("manufacturer"):
            old_val = general["manufacturer"]
            general["manufacturer"] = self.capitalize_words(str(general["manufacturer"]))
            if old_val != general["manufacturer"]:
                issues.append(f"Formatted manufacturer: '{old_val}' → '{general['manufacturer']}' in {file_name} - {model_name}")
        
        if general.get("model"):
            old_val = general["model"]
            general["model"] = self.capitalize_words(str(general["model"]))
            if old_val != general["model"]:
                issues.append(f"Formatted model: '{old_val}' → '{general['model']}' in {file_name} - {model_name}")
        
        if general.get("category"):
            old_val = general["category"]
            general["category"] = self.capitalize_words(str(general["category"]))
            if old_val != general["category"]:
                issues.append(f"Formatted category: '{old_val}' → '{general['category']}' in {file_name} - {model_name}")
        
        if general.get("subcategory"):
            old_val = general["subcategory"]
            general["subcategory"] = self.capitalize_words(str(general["subcategory"]))
            if old_val != general["subcategory"]:
                issues.append(f"Formatted subcategory: '{old_val}' → '{general['subcategory']}' in {file_name} - {model_name}")
        
        # Year should be integer
        if general.get("year"):
            try:
                if not isinstance(general["year"], int):
                    old_val = general["year"]
                    general["year"] = int(general["year"])
                    issues.append(f"Converted year to integer: {old_val} → {general['year']} in {file_name} - {model_name}")
            except (ValueError, TypeError):
                issues.append(f"Invalid year value '{general['year']}' in {file_name} - {model_name}, setting to None")
                general["year"] = None
        
        # MSRP should be int or float
        if "msrp" in general:
            try:
                msrp_val = general["msrp"]
                if isinstance(msrp_val, str):
                    msrp_val = msrp_val.replace(',', '').strip()
                    if msrp_val:
                        msrp_float = float(msrp_val)
                        if msrp_float.is_integer():
                            general["msrp"] = int(msrp_float)
                        else:
                            general["msrp"] = msrp_float
                        issues.append(f"Formatted MSRP: {general.get('msrp')} in {file_name} - {model_name}")
                    else:
                        general["msrp"] = 0
                elif msrp_val is None:
                    general["msrp"] = 0
            except (ValueError, TypeError):
                issues.append(f"Invalid MSRP value '{general.get('msrp')}' in {file_name} - {model_name}, setting to 0")
                general["msrp"] = 0
        
        # Countries should only be US and CA
        valid_countries = ["US", "CA"]
        if "countries" in general:
            if general["countries"] and isinstance(general["countries"], list):
                original_countries = general["countries"].copy()
                filtered_countries = [c for c in general["countries"] if c in valid_countries]
                if not filtered_countries:
                    general["countries"] = ["US", "CA"]
                    issues.append(f"No valid countries found, set to default ['US', 'CA'] in {file_name} - {model_name}")
                elif filtered_countries != original_countries:
                    general["countries"] = filtered_countries
                    removed = [c for c in original_countries if c not in filtered_countries]
                    issues.append(f"Removed invalid countries {removed} in {file_name} - {model_name}")
            else:
                general["countries"] = ["US", "CA"]
                issues.append(f"Empty or invalid countries, set to default ['US', 'CA'] in {file_name} - {model_name}")
        else:
            general["countries"] = ["US", "CA"]
            issues.append(f"Missing countries field, set to default ['US', 'CA'] in {file_name} - {model_name}")
        
        return general, issues
    
    def format_media_urls(self, model, file_name, model_name):
        """Format and validate media URLs (images, videos, attachments)."""
        issues = []
        
        # Images
        if "images" in model and model["images"]:
            if isinstance(model["images"], list):
                valid_images = []
                for idx, img in enumerate(model["images"]):
                    if isinstance(img, dict) and "src" in img:
                        if self.validate_url(img["src"]):
                            # Ensure all required fields exist (can be empty strings)
                            if "desc" not in img:
                                img["desc"] = ""
                            if "longDesc" not in img:
                                img["longDesc"] = ""
                            valid_images.append(img)
                        else:
                            issues.append(f"Invalid image URL removed at index {idx} in {file_name} - {model_name}")
                    elif isinstance(img, str):
                        if self.validate_url(img):
                            valid_images.append({"src": img, "desc": "", "longDesc": ""})
                        else:
                            issues.append(f"Invalid image URL string removed at index {idx} in {file_name} - {model_name}")
                model["images"] = valid_images if valid_images else None
        
        # Videos (same structure as images: src, desc, longDesc)
        if "videos" in model and model["videos"]:
            if isinstance(model["videos"], list):
                valid_videos = []
                for idx, vid in enumerate(model["videos"]):
                    if isinstance(vid, dict):
                        # Check for different URL key variations
                        url_key = None
                        if "src" in vid:
                            url_key = "src"
                        elif "videoLocation" in vid:
                            url_key = "videoLocation"
                        
                        if url_key and self.validate_url(vid[url_key]):
                            # Ensure src is the key (convert from videoLocation if needed)
                            if url_key == "videoLocation":
                                vid["src"] = vid.pop("videoLocation")
                            # Convert old keys to new standard keys if present
                            if "videoDescription" in vid:
                                vid["desc"] = vid.pop("videoDescription")
                            if "videoName" in vid:
                                vid["longDesc"] = vid.pop("videoName")
                            # Ensure all required fields exist (can be empty strings)
                            if "desc" not in vid:
                                vid["desc"] = ""
                            if "longDesc" not in vid:
                                vid["longDesc"] = ""
                            valid_videos.append(vid)
                        else:
                            issues.append(f"Invalid video URL removed at index {idx} in {file_name} - {model_name}")
                    elif isinstance(vid, str):
                        if self.validate_url(vid):
                            valid_videos.append({"src": vid, "desc": "", "longDesc": ""})
                        else:
                            issues.append(f"Invalid video URL string removed at index {idx} in {file_name} - {model_name}")
                model["videos"] = valid_videos if valid_videos else None
        
        # Attachments
        if "attachments" in model and model["attachments"]:
            if isinstance(model["attachments"], list):
                valid_attachments = []
                pdf_counter = 1
                for idx, att in enumerate(model["attachments"]):
                    if isinstance(att, dict):
                        url_key = "attachmentLocation" if "attachmentLocation" in att else "src"
                        if url_key in att and att[url_key] and self.validate_url(att[url_key]):
                            # Ensure attachmentLocation is the key (convert from src if needed)
                            if url_key == "src":
                                att["attachmentLocation"] = att.pop("src")
                            # attachmentDescription must not be empty - use pdf counter
                            if "attachmentDescription" not in att or not att["attachmentDescription"]:
                                att["attachmentDescription"] = f"pdf {pdf_counter}"
                            # attachmentName can be empty (default)
                            if "attachmentName" not in att:
                                att["attachmentName"] = ""
                            valid_attachments.append(att)
                            pdf_counter += 1
                        else:
                            issues.append(f"Invalid or empty attachment URL removed at index {idx} in {file_name} - {model_name}")
                    elif isinstance(att, str):
                        if att and self.validate_url(att):
                            valid_attachments.append({
                                "attachmentLocation": att,
                                "attachmentDescription": f"pdf {pdf_counter}",
                                "attachmentName": ""
                            })
                            pdf_counter += 1
                        else:
                            issues.append(f"Invalid or empty attachment URL string removed at index {idx} in {file_name} - {model_name}")
                model["attachments"] = valid_attachments if valid_attachments else None
        
        return model, issues
    
    def format_lists(self, model, file_name, model_name):
        """Clean features and options lists."""
        issues = []
        
        # Features
        if "features" in model and model["features"]:
            original_count = len(model["features"]) if isinstance(model["features"], list) else 0
            model["features"] = self.clean_empty_elements(model["features"])
            new_count = len(model["features"]) if model["features"] else 0
            if original_count != new_count:
                issues.append(f"Removed {original_count - new_count} empty feature(s) in {file_name} - {model_name}")
        
        # Options
        if "options" in model and model["options"]:
            original_count = len(model["options"]) if isinstance(model["options"], list) else 0
            model["options"] = self.clean_empty_elements(model["options"])
            new_count = len(model["options"]) if model["options"] else 0
            if original_count != new_count:
                issues.append(f"Removed {original_count - new_count} empty option(s) in {file_name} - {model_name}")
        
        return model, issues
    
    def format_specifications(self, model, file_name, model_name):
        """Format specification sections."""
        issues = []
        
        spec_sections = ["engine", "operational", "measurements", "hydraulics", "weights", 
                        "dimensions", "electrical", "drivetrain", "body", "other"]
        
        for section in spec_sections:
            if section in model and model[section]:
                if isinstance(model[section], dict):
                    formatted_section = {}
                    for key, value in model[section].items():
                        if isinstance(value, dict) and "label" in value and "desc" in value:
                            # Normalize units in description
                            if value["desc"]:
                                old_desc = value["desc"]
                                value["desc"] = self.normalize_units(str(value["desc"]))
                                if old_desc != value["desc"]:
                                    issues.append(f"Normalized units in {section}.{key} in {file_name} - {model_name}")
                            
                            # Ensure proper camelCase key
                            proper_key = self.camel_case(key)
                            formatted_section[proper_key] = value
                        else:
                            formatted_section[key] = value
                    
                    model[section] = formatted_section if formatted_section else None
        
        return model, issues
    
    def remove_null_fields(self, model):
        """Remove null/None fields from model, but keep required empty strings in media."""
        # Fields that should be kept even if empty string
        keep_empty_fields = {
            "desc", "longDesc",  # for images and videos (same structure)
            "attachmentName"  # for attachments (attachmentDescription should never be empty)
        }
        
        def clean_dict(d, parent_key=None):
            if isinstance(d, dict):
                cleaned = {}
                for k, v in d.items():
                    # Keep empty strings for specific media fields
                    if k in keep_empty_fields and v == "":
                        cleaned[k] = v
                    # Remove null, empty strings (except keep_empty_fields), and empty arrays
                    elif v is not None and v != [] and not (v == "" and k not in keep_empty_fields):
                        cleaned[k] = clean_dict(v, k)
                return cleaned
            elif isinstance(d, list):
                cleaned = [clean_dict(v) for v in d if v is not None and v != "" and v != []]
                return cleaned if cleaned else None
            else:
                return d
        
        return clean_dict(model)
    
    def format_model(self, model, file_name="unknown"):
        """Format a single model according to all rules."""
        issues = []
        
        try:
            # Get model name first (before formatting)
            model_name = self.get_model_name(model)
            
            # Format general section
            if "general" in model:
                model["general"], gen_issues = self.format_general_section(model["general"], file_name, model_name)
                issues.extend(gen_issues)
                # Update model_name after formatting
                model_name = self.get_model_name(model)
            else:
                issues.append(f"Missing 'general' section in {file_name} - {model_name}")
            
            # Format media URLs
            model, media_issues = self.format_media_urls(model, file_name, model_name)
            issues.extend(media_issues)
            
            # Clean lists
            model, list_issues = self.format_lists(model, file_name, model_name)
            issues.extend(list_issues)
            
            # Format specifications
            model, spec_issues = self.format_specifications(model, file_name, model_name)
            issues.extend(spec_issues)
            
            # Remove null fields
            model = self.remove_null_fields(model)
            
            self.report["processed_models"] += 1
            
            # Group issues by model name
            if issues:
                if model_name not in self.report["issues_by_model"]:
                    self.report["issues_by_model"][model_name] = []
                self.report["issues_by_model"][model_name].extend(issues)
            
            return model, True
            
        except Exception as e:
            error_msg = f"Error processing model in {file_name} - {model_name}: {str(e)}"
            self.report["errors"].append(error_msg)
            self.report["failed_models"] += 1
            return model, False
    
    def process_json_data(self, json_data, file_name="unknown"):
        """Process JSON data (can be list or single object)."""
        if isinstance(json_data, list):
            self.report["total_models"] += len(json_data)
            formatted_models = []
            for model in json_data:
                formatted_model, success = self.format_model(model, file_name)
                if success:
                    formatted_models.append(formatted_model)
            return formatted_models
        else:
            self.report["total_models"] += 1
            formatted_model, success = self.format_model(json_data, file_name)
            return [formatted_model] if success else []
    
    def generate_report(self):
        """Generate a formatted report with issues grouped by model."""
        # Count total issues
        total_issues = sum(len(issues) for issues in self.report['issues_by_model'].values())
        
        report_text = f"""
# JSON Formatting & Validation Report
**Generated on:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Summary
- **Total Models Processed:** {self.report['total_models']}
- **Successfully Formatted:** {self.report['processed_models']}
- **Failed Models:** {self.report['failed_models']}
- **Total Issues Fixed:** {total_issues}

---

## Issues Fixed by Model
"""
        if self.report['issues_by_model']:
            for model_name, issues in self.report['issues_by_model'].items():
                report_text += f"\n### 📌 {model_name}\n"
                report_text += f"**Total Issues:** {len(issues)}\n\n"
                for idx, issue in enumerate(issues, 1):
                    # Remove the file name and model name from the issue text for cleaner display
                    clean_issue = issue.split(" in ")[0] if " in " in issue else issue
                    report_text += f"{idx}. {clean_issue}\n"
                report_text += "\n"
        else:
            report_text += "\n✅ No issues found - all models are already properly formatted!\n"
        
        report_text += "\n---\n\n## Errors\n"
        if self.report['errors']:
            for error in self.report['errors']:
                report_text += f"- ❌ {error}\n"
        else:
            report_text += "\n✅ No errors encountered!\n"
        
        return report_text


# Upload Section
st.markdown("### 📤 Upload Files")
st.markdown("""
Upload one or more files:
- **Single or multiple JSON files** (`.json`)
- **Compressed archives** (`.zip`, `.tar`, `.tar.gz`) containing JSON files
""")

uploaded_files = st.file_uploader(
    "Choose file(s)",
    type=["json", "zip", "tar", "gz"],
    accept_multiple_files=True,
    help="Upload JSON files or compressed archives (ZIP, TAR, TAR.GZ)"
)

# Categorize uploaded files by type
json_files = []
archive_files = []

if uploaded_files:
    for file in uploaded_files:
        if file.name.endswith('.json'):
            json_files.append(file)
        elif file.name.endswith(('.zip', '.tar', '.tar.gz', '.gz')):
            archive_files.append(file)

# Main Logic
if uploaded_files:
    formatter = JSONFormatter()
    all_formatted_data = []
    
    try:
        # Handle JSON files
        for uploaded_file in json_files:
            try:
                json_data = json.load(uploaded_file)
                formatted_data = formatter.process_json_data(json_data, uploaded_file.name)
                all_formatted_data.extend(formatted_data)
            except json.JSONDecodeError:
                formatter.report["errors"].append(f"Invalid JSON in file: {uploaded_file.name}")
        
        # Handle compressed archives
        for archive_file in archive_files:
            if archive_file.name.endswith(".zip"):
                # ZIP archive
                archive_bytes = archive_file.read()
                archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
                file_list = [f for f in archive.namelist() if f.endswith(".json") and "__MACOSX" not in f]
                
                for file_name in file_list:
                    try:
                        with archive.open(file_name) as f:
                            json_data = json.load(io.TextIOWrapper(f, encoding='utf-8'))
                            formatted_data = formatter.process_json_data(json_data, file_name)
                            all_formatted_data.extend(formatted_data)
                    except json.JSONDecodeError:
                        formatter.report["errors"].append(f"Invalid JSON in file: {file_name}")
                        
            else:
                # TAR archive (handles .tar, .tar.gz, .gz)
                archive_bytes = archive_file.read()
                mode = "r:gz" if archive_file.name.endswith((".tar.gz", ".gz")) else "r"
                with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode=mode) as archive:
                    for member in archive.getmembers():
                        if member.name.endswith(".json") and "__MACOSX" not in member.name:
                            try:
                                f = archive.extractfile(member)
                                json_data = json.load(io.TextIOWrapper(f, encoding='utf-8'))
                                formatted_data = formatter.process_json_data(json_data, member.name)
                                all_formatted_data.extend(formatted_data)
                            except json.JSONDecodeError:
                                formatter.report["errors"].append(f"Invalid JSON in file: {member.name}")
        
        # Display results
        st.markdown("---")
        
        if all_formatted_data:
            st.success(f"✅ Successfully processed {formatter.report['processed_models']} model(s)!")
            
            if formatter.report['failed_models'] > 0:
                st.warning(f"⚠️ {formatter.report['failed_models']} model(s) failed processing.")
            
            # Report Summary
            st.markdown("### 📊 Processing Report")
            
            total_issues = sum(len(issues) for issues in formatter.report['issues_by_model'].values())
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Models", formatter.report['total_models'])
            with col2:
                st.metric("Processed", formatter.report['processed_models'])
            with col3:
                st.metric("Failed", formatter.report['failed_models'])
            with col4:
                st.metric("Issues Fixed", total_issues)
            
            # Issues Fixed - Grouped by Model
            if formatter.report['issues_by_model']:
                with st.expander(f"📋 View Issues Fixed ({total_issues} issues)", expanded=False):
                    for model_name, issues in formatter.report['issues_by_model'].items():
                        st.markdown(f"##### 📌 **{model_name}**")
                        st.markdown(f"*Total Issues: {len(issues)}*")
                        for idx, issue in enumerate(issues, 1):
                            # Clean up issue text by removing file name and model name for display
                            clean_issue = issue.split(" in ")[0] if " in " in issue else issue
                            st.markdown(f"{idx}. {clean_issue}")
                        st.markdown("---")
            else:
                st.info("✅ No issues found - all models are already properly formatted!")
            
            # Errors - Collapsible Section
            if formatter.report['errors']:
                with st.expander(f"⚠️ View Errors ({len(formatter.report['errors'])} errors)", expanded=False):
                    for error in formatter.report['errors']:
                        st.markdown(f"- ❌ {error}")
            
            st.markdown("---")
            
            # Preview formatted JSON
            if st.checkbox("Preview Formatted JSON", help="Check to view the formatted JSON data"):
                st.json(all_formatted_data)
            
            st.markdown("---")
            
            # Download buttons
            st.markdown("### 📥 Download Results")
            col1, col2 = st.columns(2)
            
            with col1:
                formatted_json_str = json.dumps(all_formatted_data, indent=4, ensure_ascii=False)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                st.download_button(
                    label="📥 Download Formatted JSON",
                    data=formatted_json_str.encode('utf-8'),
                    file_name=f"formatted_json_{timestamp}.json",
                    mime="application/json; charset=utf-8"
                )
            
            with col2:
                report = formatter.generate_report()
                st.download_button(
                    label="📄 Download Report",
                    data=report.encode('utf-8'),
                    file_name=f"formatting_report_{timestamp}.txt",
                    mime="text/plain; charset=utf-8"
                )
        else:
            st.error("❌ No valid models found or all models failed processing.")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.exception(e)

else:
    st.info("👆 Please upload file(s) using one of the tabs above to begin processing.")

