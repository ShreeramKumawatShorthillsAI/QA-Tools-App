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
This tool merges multiple JSON files from compressed archives into a single JSON file.

### Instructions
- **Upload**: A compressed archive (`.zip`, `.tar`, `.tar.gz`) containing multiple `.json` files.
- **Process**: The tool combines all valid JSON data into a single list of models.
- **Download**: Get the merged JSON file.
""")

# Create a narrower column for the file uploader
col1, col2 = st.columns([1, 1])
with col1:
    uploaded_file = st.file_uploader("Upload a compressed archive", type=["zip", "tar", "tar.gz"])

if uploaded_file:
    json_data = []  # Single list to hold all models
    invalid_files = []

    # Process the uploaded compressed file
    archive_bytes = uploaded_file.read()
    if uploaded_file.name.endswith(".zip"):
        archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
        file_list = [f for f in archive.namelist() if f.endswith(".json") and "__MACOSX" not in f]
        for file_name in file_list:
            try:
                with archive.open(file_name) as f:
                    file_content = json.load(io.TextIOWrapper(f, encoding='utf-8'))
                    # Assuming file_content is a list of models, extend the main list
                    if isinstance(file_content, list):
                        json_data.extend(file_content)
                    else:
                        json_data.append(file_content)  # Handle case if single object
            except json.JSONDecodeError:
                invalid_files.append(file_name)
    else:  # .tar or .tar.gz
        mode = "r:gz" if uploaded_file.name.endswith(".gz") else "r"
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode=mode) as archive:
            for member in archive.getmembers():
                if member.name.endswith(".json") and "__MACOSX" not in member.name:
                    try:
                        f = archive.extractfile(member)
                        file_content = json.load(io.TextIOWrapper(f, encoding='utf-8'))
                        # Assuming file_content is a list of models, extend the main list
                        if isinstance(file_content, list):
                            json_data.extend(file_content)
                        else:
                            json_data.append(file_content)  # Handle case if single object
                    except json.JSONDecodeError:
                        invalid_files.append(member.name)

    # Display results
    if json_data:
        st.success(f"Processed {len(json_data)} valid model(s) from the archive.")
        if invalid_files:
            st.warning(f"Skipped {len(invalid_files)} invalid file(s): {', '.join(invalid_files)}")

        if st.checkbox("Preview merged JSON", help="Check to view the merged JSON data"):
            st.json(json_data)

        merged_json_str = json.dumps(json_data, indent=4)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="Download Merged JSON",
            data=merged_json_str,
            file_name=f"merged_json_{timestamp}.json",
            mime="application/json"
        )
    elif invalid_files:
        st.error("No valid JSON files found in the upload.")