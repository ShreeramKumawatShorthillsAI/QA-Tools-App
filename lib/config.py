"""Configuration management for JSON Formatter & Validator."""
import os
from typing import List
from dotenv import load_dotenv
load_dotenv()

# Get API keys from environment variables
GEMINI_API_KEY_1 = os.getenv("GEMINI_API_KEY_1")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2")
GEMINI_API_KEY_3 = os.getenv("GEMINI_API_KEY_3")
GEMINI_API_KEY_4 = os.getenv("GEMINI_API_KEY_4")
GEMINI_API_KEY_5 = os.getenv("GEMINI_API_KEY_5")

class Config:
    """Application configuration."""
    
    # API Configuration
    GEMINI_API_KEYS: List[str] = [
        GEMINI_API_KEY_1,
        GEMINI_API_KEY_2,
        GEMINI_API_KEY_3,
        GEMINI_API_KEY_4,
        GEMINI_API_KEY_5
    ]
    
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

