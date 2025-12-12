"""
Configuration management for Contact Enrichment Pipeline
Load from environment variables (.env file) or credentials.json
"""

import os
import json
from pathlib import Path

# Load from .env file if present
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv not installed, use env vars directly

# ============================================================================
# Google Sheets Configuration
# ============================================================================
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', 'YOUR_GOOGLE_SHEET_ID')

# Path to Google service account credentials JSON file
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', str(Path(__file__).parent / 'credentials.json'))

# Google Sheets API scopes
GOOGLE_SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# ============================================================================
# MongoDB Configuration
# ============================================================================
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'contact_enrichment')
MONGO_RAW_CONTACTS_COLLECTION = os.getenv('MONGO_RAW_CONTACTS_COLLECTION', 'raw_contacts')
MONGO_ENRICHED_CONTACTS_COLLECTION = os.getenv('MONGO_ENRICHED_CONTACTS_COLLECTION', 'enriched_contacts')

# ============================================================================
# Enrichment APIs Configuration
# ============================================================================
COGNISM_API_KEY = os.getenv('COGNISM_API_KEY', 'YOUR_COGNISM_API_KEY')
LUSHA_API_KEY = os.getenv('LUSHA_API_KEY', 'YOUR_LUSHA_API_KEY')
ZEROBOUNCE_API_KEY = os.getenv('ZEROBOUNCE_API_KEY', 'YOUR_ZEROBOUNCE_API_KEY')
APOLLO_API_KEY = os.getenv('APOLLO_API_KEY', 'YOUR_APOLLO_API_KEY')

# ============================================================================
# Pipeline Configuration
# ============================================================================
# Number of people to find per company domain
PEOPLE_PER_COMPANY = int(os.getenv('PEOPLE_PER_COMPANY', '5'))

# Enrichment API timeouts (in seconds)
API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))

# Batch processing
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))

# Retry configuration
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '2'))

# ============================================================================
# Google Sheet Configuration
# ============================================================================
INPUT_SHEET_NAME = os.getenv('INPUT_SHEET_NAME', 'UAE')
OUTPUT_SHEET_NAME = os.getenv('OUTPUT_SHEET_NAME', 'API enriched contacts')

# Column headers for input
SHEET_INPUT_COLUMNS = {
    'company_name': 'Company name',
    'domain': 'Domain',
}

# Column headers for output (each company will have 5 people or whatever found)
SHEET_OUTPUT_COLUMNS = {
    'company_name': 'Company name',
    'domain': 'Domain',
    'first_name': 'First Name',
    'last_name': 'Last Name',
    'full_name': 'Full Name',
    'designation': 'Designation',
    'linkedin_link': 'Linkedin Link',
    'email': 'Email',
    'phone_number_1': 'Phone number 1',
    'phone_number_2': 'Phone number 2',
    'board_line': 'Board line',
    'source_of_enrichment': 'Source of Enrichment',
    'date_of_enrichment': 'Date of Enrichment',
}

# ============================================================================
# Contact Search Filters (Based on Lusha API)
# ============================================================================
# Max contacts to find per company
MAX_CONTACTS_PER_COMPANY = int(os.getenv('MAX_CONTACTS_PER_COMPANY', '10'))

# ===== LOCATION FILTERS =====
# Region: France (Germany in the future)
CONTACT_LOCATION_COUNTRY = os.getenv('CONTACT_LOCATION_COUNTRY', 'France')
CONTACT_LOCATION_CITY = os.getenv('CONTACT_LOCATION_CITY', '')  # Empty = all cities
CONTACT_LOCATION_STATE = os.getenv('CONTACT_LOCATION_STATE', '')  # Empty = all states

# ===== INCLUDE FILTERS (Contacts MUST match these) =====
# Departments: "Finance", "Information Technology", "Engineering & Technical",
#              "Marketing", "Sales", "Operations", "Human Resources", "Customer Service"
INCLUDE_DEPARTMENTS = [
    "Finance",
    "Information Technology"
]

# Seniority: "1" (Entry), "2" (Junior), "3" (Senior), "4" (Manager),
#            "5" (Director), "6" (VP), "7" (C-Level), "8" (Partner), "9" (Founder)
INCLUDE_SENIORITY = ["5", "6", "7"]  # Director, VP, C-Level

# Job Title Keywords (case-insensitive) - Right Designations to Target
INCLUDE_JOB_TITLES = [
    "IT Head",
    "Chief Financial Officer (CFO)",
    "CFO",
    "Finance Controller",
    "Finance Head",
    "Vice President – Finance",
    "Vice President of Finance",
    "Tax Head",
    "Indirect Tax Manager",
    "Tax Manager",
    "Senior Tax Manager",
    "Group Financial Controller",
    "Group Chief Financial Officer",
    "Tax Senior Manager",
    "Information Technology Manager",
    "VP Finance",
    "Finance Manager",
    "Accounting Head",
    "Accountant",
    "DAF",
    "Directeur Administratif et Financier",
    "contrôleur financier",
    "ERP Head",
    "Compliance"
]

# Required Data Points
REQUIRED_DATA_POINTS = ["work_email"]

# ===== EXCLUDE FILTERS (Contacts will be excluded if they match) =====
# Exclude Departments
EXCLUDE_DEPARTMENTS = ["Human Resources"]

# Exclude Seniority
EXCLUDE_SENIORITY = ["1", "2", "3"]  # Entry, Junior, Senior

# Exclude Job Titles (Keywords) - ICP Designations to Avoid
EXCLUDE_JOB_TITLES = [
    "Audit",
    "Corporate Finance",
    "Business Finance",
    "Investments",
    "Portfolio Management",
    "Banking",
    "IT Ops",
    "CIO",
    "CTO",
    "Procurement",
    "Accounts payable",
    "HR",
    "Key Accounts",
    "Strategic Accounts",
    "Assistant",
    "Coordinator",
    "Delivery",
    "Sales",
    "Deputy",
    "Security",
    "Information Security",
    "Risk",
    "CHRO",
    "Marketing",
    "Administrative"
]

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOG_FILE = os.getenv('LOG_FILE', 'contact_enrichment.log')

# ============================================================================
# Error Handling
# ============================================================================
# Skip errors and continue processing
CONTINUE_ON_ERROR = os.getenv('CONTINUE_ON_ERROR', 'true').lower() in ('true', '1', 'yes')
