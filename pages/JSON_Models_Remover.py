import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime

# App Config
st.set_page_config(page_title="JSON Models Remover", layout="wide")
st.header("JSON Models Remover")
st.markdown("""
📦 This tool removes specific models from your merged JSON file based on an Excel file.
            
---
### 📝 Instructions
1. **Upload JSON File**: Should contain a list of objects (with a `general.model` field).
2. **Upload Excel File**: The first sheet & first column must contain model names to remove.
3. **Download**: Cleaned JSON after removal.   
---
""")

# Upload Section
st.markdown("### 📤 Upload Files")
col1, col2 = st.columns([1, 1])
with col1:
    json_file = st.file_uploader("Upload JSON File", type=["json"])
with col2:
    excel_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

# Main Logic
if json_file and excel_file:
    try:
        # Load JSON data
        json_data = json.load(json_file)

        if not isinstance(json_data, list):
            st.error("❌ JSON must contain a list of objects.")
        else:
            # Load Excel data (first sheet, first column)
            excel_data = pd.read_excel(excel_file, sheet_name=0)
            first_column = excel_data.columns[0]
            models_to_remove = excel_data[first_column].dropna().astype(str).str.strip().tolist()

            # Filter logic
            cleaned_data = []
            for item in json_data:
                model_name = item.get('general', {}).get('model', '').strip()
                if model_name not in models_to_remove:
                    cleaned_data.append(item)

            # Summary
            removed_count = len(json_data) - len(cleaned_data)
            st.success(f"✅ Removed {removed_count} model(s). Final count: {len(cleaned_data)}")

            # Preview
            if st.checkbox("Preview Cleaned JSON", help="Check to view the cleaned JSON data"):
                st.json(cleaned_data)

            # Download
            st.markdown("---")
            cleaned_json_str = json.dumps(cleaned_data, indent=4, ensure_ascii=False)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            st.download_button(
                label="📥 Download Cleaned JSON",
                data=cleaned_json_str.encode('utf-8'),
                file_name=f"cleaned_json_{timestamp}.json",
                mime="application/json; charset=utf-8"
            )

    except json.JSONDecodeError:
        st.error("❌ Invalid JSON format.")
    except Exception as e:
        st.error(f"❌ Error: {e}")

elif json_file or excel_file:
    st.info("👆 Please upload both a JSON file and an Excel file to proceed.")
else:
    st.info("👆 Please upload file(s) to begin processing.")
