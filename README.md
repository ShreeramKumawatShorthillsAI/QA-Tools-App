# QA Tools Hub

A Streamlit-based toolkit for the TI DCDE project QA team, featuring automated JSON processing, validation, and quality assurance tools.

## Features

### 1. JSON Formatter & Validator
- Validates JSON models against standard rules
- Formats and fixes common issues (units, special characters, etc.)
- Uses Google Gemini AI for intelligent text processing
- Generates detailed validation reports
- Supports batch processing with multiple API keys

### 2. JSON Merger
- Merges multiple JSON files into a single consolidated file
- Supports direct file upload or ZIP archive
- Maintains data integrity during merge
- Exports merged results

### 3. JSON Models Remover
- Removes specific models from JSON files
- Accepts model list via Excel file (.xlsx)
- Batch processing capability
- Generates cleaned output files

### 4. JSON URLs Checker
- Validates URLs from JSON files (images, attachments, products)
- Checks URL accessibility and status codes
- Generates comprehensive reports with broken link details
- Supports multiple JSON files simultaneously

## Project Structure

```
QA-Tools-App/
├── Home.py                 # Main application entry point
├── pages/                  # Streamlit pages (tools)
│   ├── JSON_Formatter_Validator.py
│   ├── JSON_Merger.py
│   ├── JSON_Models_Remover.py
│   └── JSON_URLs_Checker.py
├── lib/                    # Core libraries
│   ├── config.py          # Configuration settings
│   ├── gemini_client.py   # Google Gemini AI integration
│   ├── validators.py      # Validation rules and logic
│   ├── json_formatter.py  # JSON formatting utilities
│   ├── file_loader.py     # File handling utilities
│   ├── api_manager.py     # API key management
│   └── report_generator.py # Report generation
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd QA-Tools-App
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
streamlit run Home.py
```

The application will open in your default web browser at `https://shreeram.streamlit.app/`

## Configuration

Key settings in `lib/config.py`:
- **GEMINI_MODEL**: AI model version (default: `gemini-2.5-flash-lite`)
- **VALID_COUNTRIES**: Supported countries (US, CA)
- **BATCH_SIZE**: Number of items processed per batch
- **MAX_CALLS_PER_API_KEY**: API rate limiting

## Requirements

- Python 3.8+
- Streamlit 1.44+
- Google Gemini API access
- See `requirements.txt` for complete dependencies

## Support

For support, issues, or feedback, contact:  
📬 **shreeram@shorthills.ai**

---

**Built with ❤️ for the TI DCDE QA Team**
