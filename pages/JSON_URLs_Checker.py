import os
import json
import requests
import pandas as pd
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent
from zipfile import ZipFile
import io

# Set page configuration
st.set_page_config(page_title="JSON URLs Checker", layout="wide")

# Streamlit app
st.header("JSON URLs Checker")
st.write("Check the status of URLs (images, attachments, and products) from multiple JSON files.")

# Instructions
st.markdown("""
### Instructions
- **Upload**: One or more JSON files containing URLs.
- **Process**: The tool checks the status of all URLs (images, attachments, and products).
- **Download**: Get an Excel file with URL statuses for each JSON file, zipped together.
""")

# Initialize UserAgent safely
try:
    ua = UserAgent()
except Exception as e:
    st.warning(f"Failed to initialize UserAgent: {e}")
    ua = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

# Initialize session state for storing results
if 'processed_results' not in st.session_state:
    st.session_state['processed_results'] = {}

class URLChecker:
    def __init__(self, timeout=5, max_workers=20):
        self.timeout = timeout
        self.max_workers = max_workers

    def check_url(self, url):
        # Check a single URL and return its status
        headers = {
            "User-Agent": ua.random if isinstance(ua, UserAgent) else ua["User-Agent"],
            "Referer": "https://www.google.com/",
        }
        session = requests.Session()
        try:
            response = session.get(url, headers=headers, timeout=self.timeout, allow_redirects=False)
            if response.status_code == 200:
                return "Working"
            elif 300 <= response.status_code < 400:
                return f"Redirect - Status Code: {response.status_code}"
            elif response.status_code == 403:
                return "Blocked - Captcha Error"
            else:
                return f"Not Working - Status Code: {response.status_code}"
        except requests.exceptions.Timeout:
            return "Timeout"
        except requests.exceptions.RequestException as e:
            return f"Failed - {str(e)}"

    def process_urls(self, url_list):
        # Process a list of URLs concurrently with a progress bar
        statuses = []
        total_urls = len(url_list)
        completed_urls = 0
        progress_bar = st.progress(0)
        progress_text = st.empty()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.check_url, url): url for url in url_list if url}
            for future in as_completed(futures):
                try:
                    status = future.result()
                except Exception as e:
                    status = f"Failed - {str(e)}"
                statuses.append(status)
                completed_urls += 1
                percentage_completed = (completed_urls / total_urls) * 100
                progress_bar.progress(int(percentage_completed))
                progress_text.text(f"Processing: {percentage_completed:.2f}% complete")
        return statuses

class JSONReader:
    def __init__(self, json_content):
        self.json_content = json_content

    def read_urls(self):
        # Extract URLs and model names from JSON content
        image_urls = []
        image_models = []
        attachment_urls = []
        attachment_models = []
        product_urls = []
        product_models = []
        try:
            data = json.loads(self.json_content)
        except json.JSONDecodeError as e:
            st.error(f"Error reading JSON content: {e}")
            return [], [], [], [], [], []
        for json_model in data:
            model = json_model.get("general", {}).get("model")
            images = json_model.get("images", [])
            for image in images:
                url = image.get("src")
                if url:
                    image_urls.append(url)
                    image_models.append(model)
            attachments = json_model.get("attachments", [])
            for attachment in attachments:
                url = attachment.get("attachmentLocation")
                if url:
                    attachment_urls.append(url)
                    attachment_models.append(model)
            product_uri = json_model.get("productUri")
            if product_uri:
                product_urls.append(product_uri)
                product_models.append(model)
        return image_models, image_urls, attachment_models, attachment_urls, product_models, product_urls

class ExcelSaver:
    def __init__(self, output_file):
        self.output_file = output_file

    def save_to_excel(self, image_models, image_urls, image_statuses, attachment_models, attachment_urls, attachment_statuses, product_models, product_urls, product_statuses):
        # Save URL statuses to an in-memory Excel file
        df_images = pd.DataFrame({"Model_name": image_models, "URL": image_urls, "Status": image_statuses})
        df_attachments = pd.DataFrame({"Model_name": attachment_models, "URL": attachment_urls, "Status": attachment_statuses})
        df_products = pd.DataFrame({"Model_name": product_models, "URL": product_urls, "Status": product_statuses})
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_images.to_excel(writer, sheet_name="image_url_status", index=False)
            df_attachments.to_excel(writer, sheet_name="pdf_url_status", index=False)
            df_products.to_excel(writer, sheet_name="product_url_status", index=False)
        output.seek(0)
        st.session_state['processed_results'][self.output_file] = output
        st.success(f"Results saved to {self.output_file}")

# Create a narrower column for the file uploader
col1, col2 = st.columns([1, 1])
with col1:
    uploaded_files = st.file_uploader("Upload JSON files", type=["json"], accept_multiple_files=True)

if uploaded_files:
    url_checker = URLChecker(max_workers=20)
    results = []

    for uploaded_file in uploaded_files:
        output_file = os.path.splitext(uploaded_file.name)[0] + "_results.xlsx"
        # Check if this file is already processed
        if output_file in st.session_state['processed_results']:
            st.write(f"<h4>{uploaded_file.name} already processed</h4>", unsafe_allow_html=True)
            results.append(output_file)
            continue

        st.write(f"<h3>Processing {uploaded_file.name}</h3>", unsafe_allow_html=True)
        json_reader = JSONReader(uploaded_file.getvalue().decode('utf-8'))
        image_models, image_urls, attachment_models, attachment_urls, product_models, product_urls = json_reader.read_urls()

        total_urls = len(image_urls) + len(attachment_urls) + len(product_urls)
        st.write(f"Total URLs to check: {total_urls}")

        if not image_urls and not attachment_urls and not product_urls:
            st.warning(f"No URLs found in {uploaded_file.name}.")
            continue

        st.write("<h4>Checking image URLs...</h4>", unsafe_allow_html=True)
        image_statuses = url_checker.process_urls(image_urls)
        st.write("<h4>Checking attachment URLs...</h4>", unsafe_allow_html=True)
        attachment_statuses = url_checker.process_urls(attachment_urls)
        st.write("<h4>Checking product URLs...</h4>", unsafe_allow_html=True)
        product_statuses = url_checker.process_urls(product_urls)

        excel_saver = ExcelSaver(output_file)
        excel_saver.save_to_excel(image_models, image_urls, image_statuses, attachment_models, attachment_urls, attachment_statuses, product_models, product_urls, product_statuses)
        results.append(output_file)

    # Provide download link for all results
    if results:
        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, "w") as zipf:
            for result_file in results:
                if result_file in st.session_state['processed_results']:
                    zipf.writestr(result_file, st.session_state['processed_results'][result_file].getvalue())
        zip_buffer.seek(0)
        st.download_button(
            label="Download All Results",
            data=zip_buffer.getvalue(),
            file_name="all_results.zip",
            mime="application/zip",
            key="download_button"
        )

# Optional: Button to clear processed results
if st.button("Clear Processed Results"):
    st.session_state['processed_results'] = {}
    st.success("Cleared all processed results.")