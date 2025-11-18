"""
JSON Formatter & Validator
Refactored with OOP principles, clean architecture, and separation of concerns.
"""
import streamlit as st
import json
from datetime import datetime

from lib.config import Config
from lib.api_manager import APIKeyManager
from lib.gemini_client import GeminiAPIClient
from lib.json_formatter import JSONModelFormatter
from lib.report_generator import ReportGenerator
from lib.file_loader import FileLoader


# ==================== Page Configuration ====================
st.set_page_config(
    page_title="JSON Formatter & Validator", 
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== Header ====================
st.header("JSON Formatter & Validator")
st.markdown("""
🔧 This tool formats and validates JSON model files according to standard rules.

---

### 📝 Instructions
1. **Upload**: Single JSON file(s), multiple JSON files, or a compressed archive (`.zip`, `.tar`, `.tar.gz`)
2. **Process**: The tool will format and validate each model according to the rules.
3. **Download**: Get the cleaned JSON file and a detailed report.

---
""")


# ==================== Session State Management ====================
def initialize_session_state():
    """Initialize session state variables."""
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'formatter_report' not in st.session_state:
        st.session_state.formatter_report = None
    if 'uploaded_file_ids' not in st.session_state:
        st.session_state.uploaded_file_ids = None
    if 'api_manager' not in st.session_state:
        st.session_state.api_manager = None


initialize_session_state()


# ==================== File Upload Section ====================
st.markdown("### 📤 Upload Files")
st.markdown("""
Upload one or more files:
- **Single or multiple JSON files** (`.json`)
- **Compressed archives** (`.zip`, `.tar`, `.tar.gz`) containing JSON files
""")

col1, col2 = st.columns([1, 1])
with col1:
    uploaded_files = st.file_uploader(
        "Choose file(s)",
        type=["json", "zip", "tar", "gz"],
        accept_multiple_files=True,
        help="Upload JSON files or compressed archives (ZIP, TAR, TAR.GZ)"
    )


# ==================== Processing Logic ====================
def get_file_ids(files):
    """Generate unique IDs for uploaded files."""
    if not files:
        return None
    return tuple((f.name, f.size) for f in files)


def process_files(uploaded_files):
    """Main file processing function."""
    # Initialize API manager and clients
    if st.session_state.api_manager is None:
        st.session_state.api_manager = APIKeyManager(
            Config.GEMINI_API_KEYS, 
            Config.MAX_CALLS_PER_API_KEY
        )
    
    api_manager = st.session_state.api_manager
    gemini_client = GeminiAPIClient(api_manager, Config.GEMINI_MODEL)
    formatter = JSONModelFormatter(gemini_client)
    file_loader = FileLoader()
    
    # Categorize files
    json_files, archive_files = file_loader.categorize_files(uploaded_files)
    
    # Load all JSON data
    all_json_data = []
    
    # Load JSON files
    for json_file in json_files:
        json_data, file_name, error = file_loader.load_json_file(json_file)
        if error:
            formatter.report.add_error(error)
        else:
            all_json_data.append((json_data, file_name))
    
    # Load archive files
    for archive_file in archive_files:
        if archive_file.name.endswith(".zip"):
            results = file_loader.load_zip_archive(archive_file)
        else:
            results = file_loader.load_tar_archive(archive_file)
        
        for json_data, file_name, error in results:
            if error:
                formatter.report.add_error(error)
            else:
                all_json_data.append((json_data, file_name))
    
    if not all_json_data:
        st.error("❌ No valid JSON files found!")
        return None, None
    
    # Count total models
    total_models = sum(len(data) if isinstance(data, list) else 1 for data, _ in all_json_data)
    
    # Calculate unique model names for API call estimation
    all_model_names = []
    for json_data, _ in all_json_data:
        if isinstance(json_data, list):
            for model in json_data:
                if isinstance(model, dict) and "general" in model and "model" in model["general"]:
                    name = model["general"]["model"]
                    if name and isinstance(name, str):
                        all_model_names.append(name)
        else:
            if isinstance(json_data, dict) and "general" in json_data and "model" in json_data["general"]:
                name = json_data["general"]["model"]
                if name and isinstance(name, str):
                    all_model_names.append(name)
    
    # Count unique model names
    unique_model_names = len(set(all_model_names))
    total_api_calls = (unique_model_names + Config.BATCH_SIZE - 1) // Config.BATCH_SIZE
    estimated_time = total_api_calls * 3  # ~3 seconds per API call
    
    # Display initial info
    st.info(f"""
    📊 **Processing Information**
    - Total models to process: **{total_models}**
    - Unique model names: **{unique_model_names}**
    - Estimated API calls needed: **{total_api_calls}**
    - Estimated processing time: **~{estimated_time} seconds** ({estimated_time // 60} min {estimated_time % 60} sec)
    """)
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(current_batch, total_batches):
        progress = current_batch / total_batches
        progress_bar.progress(progress)
        status_text.text(f"⏳ Processing batch {current_batch}/{total_batches}...")
    
    # Pre-batch all model names
    with st.spinner("🔄 Processing model names..."):
        formatter.prebatch_model_names(all_json_data, progress_callback=update_progress)
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Show completion status
    status = api_manager.get_status()
    st.success(f"""
    ✅ **Batch Processing Complete!**
    - Total API calls made: **{status['total_calls']}**
    - Total API keys available: **{status['total_keys']}**
    """)
    
    # Process all models
    all_formatted_data = []
    
    with st.spinner("🔄 Formatting and validating models..."):
        for json_data, file_name in all_json_data:
            formatted_data = formatter.process_json_data(json_data, file_name)
            all_formatted_data.extend(formatted_data)
    
    return all_formatted_data, formatter.report.to_dict()


# ==================== Main Processing ====================
current_file_ids = get_file_ids(uploaded_files)

# Check if files have changed
if uploaded_files and current_file_ids != st.session_state.uploaded_file_ids:
    st.session_state.uploaded_file_ids = current_file_ids
    
    try:
        formatted_data, report = process_files(uploaded_files)
        
        if formatted_data:
            st.session_state.processed_data = formatted_data
            st.session_state.formatter_report = report
        else:
            st.session_state.processed_data = None
            st.session_state.formatter_report = None
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.exception(e)
        st.session_state.processed_data = None
        st.session_state.formatter_report = None


# ==================== Display Results ====================
if uploaded_files and st.session_state.processed_data is not None:
    formatted_data = st.session_state.processed_data
    report_data = st.session_state.formatter_report
    
    st.markdown("---")
    
    if formatted_data:
        # Success message
        st.success(f"✅ Successfully processed {report_data['processed_models']} model(s)!")
        
        if report_data['failed_models'] > 0:
            st.warning(f"⚠️ {report_data['failed_models']} model(s) failed processing.")
        
        # Summary statistics
        st.markdown("### 📊 Processing Report")
        
        stats = ReportGenerator.get_summary_stats(report_data)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Models", stats['total_models'])
        with col2:
            st.metric("Processed", stats['processed_models'])
        with col3:
            st.metric("Failed", stats['failed_models'])
        with col4:
            st.metric("Issues Fixed", stats['total_issues'])
        
        # Issues details (collapsible)
        if report_data['issues_by_model']:
            with st.expander(f"📋 View Issues Fixed ({stats['total_issues']} issues)", expanded=False):
                for model_name, issues in report_data['issues_by_model'].items():
                    st.markdown(f"##### 📌 **{model_name}**")
                    st.markdown(f"*Total Issues: {len(issues)}*")
                    
                    for idx, issue in enumerate(issues, 1):
                        clean_issue = issue.split(" in ")[0] if " in " in issue else issue
                        st.markdown(f"{idx}. {clean_issue}")
                    
                    st.markdown("---")
        else:
            st.info("✅ No issues found - all models are already properly formatted!")
        
        # Errors (collapsible)
        if report_data['errors']:
            with st.expander(f"⚠️ View Errors ({len(report_data['errors'])} errors)", expanded=False):
                for error in report_data['errors']:
                    st.markdown(f"- ❌ {error}")
        
        st.markdown("---")
        
        # Preview formatted JSON (checkbox)
        if st.checkbox("Preview Formatted JSON", help="Check to view the formatted JSON data"):
            st.json(formatted_data)
        
        st.markdown("---")
        
        # Download buttons
        st.markdown("### 📥 Download Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            formatted_json_str = json.dumps(formatted_data, indent=4, ensure_ascii=False)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            st.download_button(
                label="📥 Download Formatted JSON",
                data=formatted_json_str.encode('utf-8'),
                file_name=f"formatted_json_{timestamp}.json",
                mime="application/json; charset=utf-8"
            )
        
        with col2:
            report_text = ReportGenerator.generate_text_report(report_data)
            
            st.download_button(
                label="📄 Download Report",
                data=report_text.encode('utf-8'),
                file_name=f"formatting_report_{timestamp}.txt",
                mime="text/plain; charset=utf-8"
            )
    else:
        st.error("❌ No valid models found or all models failed processing.")

elif uploaded_files:
    with col1:
        st.info("ℹ️ Files uploaded. Processing...")
else:
    with col1:
        st.info("👆 Please upload file(s) to begin processing.")


# ==================== Footer ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <small>JSON Formatter & Validator | Built with Streamlit & Gemini AI</small>
</div>
""", unsafe_allow_html=True)

