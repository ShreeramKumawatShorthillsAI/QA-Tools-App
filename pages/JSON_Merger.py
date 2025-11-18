import streamlit as st
import json
import zipfile
import tarfile
import io
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="JSON Merger", layout="wide")

# Header
st.header("JSON Merger")
st.markdown("""
📦 This tool merges multiple **JSON files** into a single JSON file.

---

### 📝 Instructions
1. **Upload**: Single JSON file(s), multiple JSON files, or a compressed archive (`.zip`, `.tar`, `.tar.gz`)
2. **Process**: The tool combines all valid JSON data into a single list of models.
3. **Download**: Get the merged JSON file.

---
""")

# File uploader - supports both JSON files and compressed archives
st.markdown("### 📤 Upload Files")
col1, col2 = st.columns([1, 1])
with col1:
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

# Main logic
if uploaded_files:
    json_data = []
    invalid_files = []
    
    try:
        # Handle JSON files directly
        for json_file in json_files:
            try:
                file_content = json.load(json_file)
                if isinstance(file_content, list):
                    json_data.extend(file_content)
                else:
                    json_data.append(file_content)
            except json.JSONDecodeError:
                invalid_files.append(json_file.name)
        
        # Handle compressed archives
        for archive_file in archive_files:
            archive_bytes = archive_file.read()
            
            if archive_file.name.endswith(".zip"):
                # ZIP archive
                archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
                file_list = [f for f in archive.namelist() if f.endswith(".json") and "__MACOSX" not in f]
                
                for file_name in file_list:
                    try:
                        with archive.open(file_name) as f:
                            file_content = json.load(io.TextIOWrapper(f, encoding='utf-8'))
                            if isinstance(file_content, list):
                                json_data.extend(file_content)
                            else:
                                json_data.append(file_content)
                    except json.JSONDecodeError:
                        invalid_files.append(file_name)
            else:
                # TAR archive (handles .tar, .tar.gz, .gz)
                mode = "r:gz" if archive_file.name.endswith((".tar.gz", ".gz")) else "r"
                with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode=mode) as archive:
                    for member in archive.getmembers():
                        if member.name.endswith(".json") and "__MACOSX" not in member.name:
                            try:
                                f = archive.extractfile(member)
                                file_content = json.load(io.TextIOWrapper(f, encoding='utf-8'))
                                if isinstance(file_content, list):
                                    json_data.extend(file_content)
                                else:
                                    json_data.append(file_content)
                            except json.JSONDecodeError:
                                invalid_files.append(member.name)

        # Display results
        st.markdown("---")
        if json_data:
            st.success(f"✅ Processed `{len(json_data)}` valid model(s) from the uploaded files.")
            if invalid_files:
                st.warning(f"⚠️ Skipped `{len(invalid_files)}` invalid file(s): `{', '.join(invalid_files)}`")

            if st.checkbox("Preview merged JSON", help="Check to view the merged JSON data"):
                st.json(json_data)

            merged_json_str = json.dumps(json_data, indent=4, ensure_ascii=False)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            st.download_button(
                label="⬇️ Download Merged JSON",
                data=merged_json_str.encode('utf-8'),
                file_name=f"merged_json_{timestamp}.json",
                mime="application/json; charset=utf-8"
            )
        elif invalid_files:
            st.error("❌ No valid JSON files found in the upload.")
        else:
            with col1:
                st.info("👆 Please upload file(s) to begin processing.")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.exception(e)
else:
    with col1:
        st.info("👆 Please upload file(s) to begin processing.")
