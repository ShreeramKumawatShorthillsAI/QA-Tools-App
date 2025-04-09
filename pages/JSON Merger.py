import streamlit as st
import json
import zipfile
import tarfile
import io
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="JSON Merger", layout="wide")

st.header("JSON Merger Tool")
st.markdown("""
This tool merges multiple JSON files into a single JSON file.

### Instructions
- **Upload**: A single `.json` file or a compressed archive (`.zip`, `.tar`, `.tar.gz`) with multiple `.json` files.
- **Process**: The tool combines all valid JSON data into a single JSON file.
- **Download**: Get the merged JSON file.
""")

# Create a narrower column for the file uploader
col1, col2 = st.columns([1,1])  # Adjust the ratio (e.g., 1:3) to reduce width
with col1:
    uploaded_file = st.file_uploader("Upload a JSON file or archive", type=["json", "zip", "tar", "tar.gz"])

if uploaded_file:
    json_data = []
    invalid_files = []

    # Process the uploaded file
    if uploaded_file.name.endswith(".json"):
        try:
            data = json.load(io.TextIOWrapper(uploaded_file, encoding='utf-8'))
            json_data.append(data)
        except json.JSONDecodeError:
            invalid_files.append(uploaded_file.name)
    elif uploaded_file.name.endswith((".zip", ".tar", ".tar.gz")):
        # Handle archives in memory
        archive_bytes = uploaded_file.read()
        if uploaded_file.name.endswith(".zip"):
            archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
            file_list = [f for f in archive.namelist() if f.endswith(".json") and "__MACOSX" not in f]
            for file_name in file_list:
                try:
                    with archive.open(file_name) as f:
                        data = json.load(io.TextIOWrapper(f, encoding='utf-8'))
                        json_data.append(data)
                except json.JSONDecodeError:
                    invalid_files.append(file_name)
        else:  # .tar or .tar.gz
            mode = "r:gz" if uploaded_file.name.endswith(".gz") else "r"
            with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode=mode) as archive:
                for member in archive.getmembers():
                    if member.name.endswith(".json") and "__MACOSX" not in member.name:
                        try:
                            f = archive.extractfile(member)
                            data = json.load(io.TextIOWrapper(f, encoding='utf-8'))
                            json_data.append(data)
                        except json.JSONDecodeError:
                            invalid_files.append(member.name)

    # Display results
    if json_data:
        st.success(f"Processed {len(json_data)} valid JSON file(s).")
        if invalid_files:
            st.warning(f"Skipped {len(invalid_files)} invalid file(s): {', '.join(invalid_files)}")

        # Add JSON preview option
        if st.checkbox("Preview merged JSON", help="Check to view the merged JSON data"):
            st.json(json_data)

        # Prepare merged JSON
        merged_json_str = json.dumps(json_data, indent=4)
        
        # Download button
        timestamp = datetime.now().strftime('%d_%m_%Y')
        st.download_button(
            label="Download Merged JSON",
            data=merged_json_str,
            file_name=f"merged_json_{timestamp}.json",
            mime="application/json"
        )
    elif invalid_files:
        st.error("No valid JSON files found in the upload.")