"""
Configuration settings for the WeCare application.
Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from typing import Dict, Any, List

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent

# OpenAI API settings
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "wecare/gpt-4o")
LLM_API_BASE_URL = os.environ.get("LLM_API_BASE_URL", "https://llm.swe.along.pw")

# Scoring settings
SCORING_ENABLED = os.environ.get("SCORING_ENABLED", "True").lower() == "true"

# Common dietary preferences
COMMON_DIETS = [
    "Vegetarian",
    "Vegan",
    "Gluten-Free",
    "Keto",
    "Low-Sugar",
    "Low-Carb",
    "Low-Fat",
    "Low-Sodium",
    "Lactose-Free",
    "Pescatarian",
    "Paleo"
]

# Common food allergens
COMMON_ALLERGENS = [
    "Peanuts",
    "Tree Nuts",
    "Milk",
    "Eggs",
    "Wheat",
    "Soy",
    "Fish",
    "Shellfish",
    "Sesame",
    "Mustard",
    "Celery",
    "Lupin",
    "Sulfites",
    "Mollusks"
]

# These are just placeholder values for configuration
SAFE_ADDITIVES = [
    "E100", "E101", "E300", "E304", "E306", "E307", "E308", 
    "E309", "E322", "E330", "E331", "E332", "E333", "E334"
]

SUSPICIOUS_ADDITIVES = [
    "E102", "E104", "E110", "E122", "E124", "E129", "E211", 
    "E249", "E250", "E251", "E252", "E621", "E920", "E954"
]

HARMFUL_ADDITIVES = [
    "E102", "E104", "E110", "E122", "E124", "E129", "E211", 
    "E249", "E250", "E251", "E252", "E621", "E920", "E954"
]

# Logging settings
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "wecare": {
            "handlers": ["console"],
            "level": os.environ.get("WECARE_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
} 