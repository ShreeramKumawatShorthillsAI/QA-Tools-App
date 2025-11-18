"""Configuration management for JSON Formatter & Validator."""
import os
from typing import List
from dotenv import load_dotenv

# Try to import streamlit for cloud deployment
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# Load .env file for local development
load_dotenv()


def get_api_keys() -> List[str]:
    """
    Get API keys from either Streamlit secrets (cloud) or environment variables (local).
    Supports both deployment methods seamlessly.
    
    Returns:
        List of API keys (filters out None values)
    """
    api_keys = []
    
    # Try Streamlit secrets first (for cloud deployment)
    if STREAMLIT_AVAILABLE:
        try:
            # Access secrets from st.secrets
            api_keys = [
                st.secrets.GEMINI_API_KEY_1,
                st.secrets.GEMINI_API_KEY_2,
                st.secrets.GEMINI_API_KEY_3,
                st.secrets.GEMINI_API_KEY_4,
                st.secrets.GEMINI_API_KEY_5,
            ]
            # Filter out None values and return
            api_keys = [key for key in api_keys if key]
            if api_keys:
                print("✅ Loaded API keys from Streamlit secrets")
                return api_keys
        except Exception as e:
            print(f"⚠️  Could not load from Streamlit secrets: {e}")
    
    # Fallback to environment variables (for local development)
    api_keys = [
        os.getenv("GEMINI_API_KEY_1"),
        os.getenv("GEMINI_API_KEY_2"),
        os.getenv("GEMINI_API_KEY_3"),
        os.getenv("GEMINI_API_KEY_4"),
        os.getenv("GEMINI_API_KEY_5"),
    ]
    
    # Filter out None values
    api_keys = [key for key in api_keys if key]
    
    if api_keys:
        print("✅ Loaded API keys from environment variables (.env)")
    else:
        print("❌ No API keys found! Please configure them in .env or secrets.toml")
    
    return api_keys


class Config:
    """Application configuration."""
    
    # API Configuration - dynamically loaded based on environment
    GEMINI_API_KEYS: List[str] = get_api_keys()
    
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    MAX_CALLS_PER_API_KEY: int = 15
    BATCH_SIZE: int = 30
    
    # Validation Rules
    VALID_COUNTRIES: List[str] = ["US", "CA"]
    
    UNIT_REPLACEMENTS: dict = {
        "in.": "in", "ft.": "ft", "FT.": "FT", "Ft.": "Ft", "yd.": "yd",
        "mi.": "mi", "cm.": "cm", "mm.": "mm", "m.": "m",
        "max.": "max", "Max.": "Max", "min.": "min", "Min.": "Min",
        "avg.": "avg", "Avg.": "Avg", "nom.": "nom", "Nom.": "Nom",
        "lbs.": "lbs", "lb.": "lb", "oz.": "oz",
        "cu.": "cu", "gal.": "gal", "qt.": "qt", "pt.": "pt",
        "sec.": "sec", "Sec.": "Sec", "hr.":     "hr", "hrs.": "hr",
        "°F.": "°F", "°C.": "°C"
    }
    
    SPEC_SECTIONS: List[str] = [
        "engine", "operational", "measurements", "hydraulics", 
        "weights", "dimensions", "electrical", "drivetrain", 
        "body", "other"
    ]
    
    REQUIRED_GENERAL_FIELDS: List[str] = [
        "manufacturer", "model", "year", "msrp", 
        "category", "subcategory", "description", "countries"
    ]
    
    MEDIA_EMPTY_FIELDS: set = {"desc", "longDesc", "attachmentName"}

