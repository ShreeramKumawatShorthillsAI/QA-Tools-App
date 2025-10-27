import streamlit as st

# Set page configuration for a wide layout
st.set_page_config(page_title="QA Tools Hub", layout="wide")

# Title and Introduction
st.title("QA Tools Hub")
st.markdown("""
👋 Welcome to the **QA Tools Hub**! This application provides a suite of tools designed to assist the QA team in their daily tasks.

---

### 🧰 Available Tools
1. **JSON Formatter & Validator**: Format and validate JSON models according to standard rules with detailed reporting.
2. **JSON Merger**: Merge multiple JSON files from a single file or archive into one JSON file.
3. **JSON Models Remover**: Remove models from JSON files.
4. **JSON URLs Checker**: Check the status of URLs (images, attachments, and products) from multiple JSON files.

---

📬 For support or feedback, contact **shreeram@shorthills.ai**
""")