# Contact Enrichment Pipeline

Production-level LangGraph pipeline for enriching contact data using multiple B2B databases and email verification services.

## Features

- **Multi-source enrichment**: Cognism, Lusha, Apollo B2B databases
- **Email verification**: ZeroBounce integration
- **Batch processing**: Find 5-6 people per company domain
- **Data persistence**: MongoDB + Google Sheets
- **Error handling**: Configurable continue-on-error behavior
- **Async execution**: Parallel API calls for performance
- **Comprehensive logging**: File and console logging

## Project Structure

```
contact_enrichment/
├── src/                           ← Source code
│   ├── __init__.py
│   ├── pipeline.py               ← LangGraph workflow
│   ├── models/                   ← Data models
│   │   └── __init__.py
│   ├── services/                 ← External integrations
│   │   ├── __init__.py
│   │   ├── sheets.py            ← Google Sheets
│   │   ├── mongodb.py           ← MongoDB
│   │   └── enrichment_apis.py   ← APIs (Cognism, Lusha, Apollo, ZeroBounce)
│   └── utils/                    ← Utilities
│       ├── __init__.py
│       └── logging_config.py    ← Logging setup
│
├── config.py                      ← Configuration (APIs, DB, sheets)
├── main.py                        ← Entry point
├── example.py                     ← Usage examples
├── requirements.txt               ← Dependencies
├── README.md                      ← This file
└── .gitignore
```

## Architecture Flow

```
main.py
    ↓
config.py (Load credentials & settings)
    ↓
src/pipeline.py (LangGraph workflow)
    ├── load_companies (Google Sheets)
    ├── search_cognism (Parallel APIs)
    ├── search_lusha
    ├── search_apollo
    ├── deduplicate_employees
    ├── verify_emails (ZeroBounce)
    ├── store_in_mongodb (MongoDB)
    └── update_google_sheet (Google Sheets)
    ↓
src/services/
    ├── sheets.py (Google Sheets Service)
    ├── mongodb.py (MongoDB Service)
    └── enrichment_apis.py (API Clients)
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

Edit `config.py` and set:

```python
# Google Sheets
GOOGLE_SHEET_ID = "your-sheet-id"
GOOGLE_CREDENTIALS_JSON = """
{
  "type": "service_account",
  ...
}
"""

# MongoDB
MONGO_URI = "mongodb+srv://user:pass@cluster.mongodb.net/"

# Enrichment APIs
COGNISM_API_KEY = "your-key"
LUSHA_API_KEY = "your-key"
APOLLO_API_KEY = "your-key"
ZEROBOUNCE_API_KEY = "your-key"
```

### 3. Prepare Google Sheet

Your input Google Sheet should have columns:
- `company_name` - Company name
- `domain` - Company domain (e.g., google.com)
- `name` - Contact name (optional)
- `email` - Contact email (optional)
- `phone` - Contact phone (optional)
- `linkedin_url` - LinkedIn profile (optional)
- `job_title` - Job title (optional)
- `department` - Department (optional)
- `seniority` - Seniority level (optional)

### 4. MongoDB Setup

Create a MongoDB instance (local or Atlas):

```bash
# Local MongoDB
mongod

# Or MongoDB Atlas: https://www.mongodb.com/cloud/atlas
```

## Usage

### Run Pipeline

```bash
python main.py
```

### Expected Output

```
======================================================================
CONTACT ENRICHMENT PIPELINE
======================================================================
✓ Configuration validated
✓ Loaded 5 companies
✓ Cognism: Found 6 people for company.com
✓ Lusha: Found 5 people for company.com
✓ Apollo: Found 6 people for company.com
✓ ZeroBounce: Validated john@company.com
✓ Stored 6 contacts in MongoDB
✓ Appended 6 rows to Google Sheet

======================================================================
EXECUTION SUMMARY
======================================================================
Status: ✓ SUCCESS
Total Contacts Enriched: 30
Valid Emails: 28
Errors: 0
======================================================================
```

## Configuration Options

Edit `config.py` to customize:

```python
PEOPLE_PER_COMPANY = 5          # Find 5-6 people per company
API_TIMEOUT = 30                # API timeout in seconds
BATCH_SIZE = 10                 # Batch processing size
CONTINUE_ON_ERROR = True        # Continue on API failures
LOG_LEVEL = "INFO"              # Logging level
```

## Data Flow

1. **Load Companies**: Read unique companies from Google Sheet
2. **Search Employees**: Query Cognism, Lusha, Apollo in parallel for each company
3. **Deduplicate**: Remove duplicate emails, keep top N
4. **Verify Emails**: Validate emails with ZeroBounce
5. **Store MongoDB**: Save enriched contacts to MongoDB
6. **Update Sheet**: Append new rows with enriched data to Google Sheet

## Error Handling

- API failures are logged and optionally skipped
- Set `CONTINUE_ON_ERROR = True` to skip failed APIs
- All errors are recorded in `errors` list
- Logs saved to `contact_enrichment.log`

## Database Schema

### MongoDB - enriched_contacts

```json
{
  "_id": ObjectId,
  "company_name": "String",
  "domain": "String",
  "name": "String",
  "enriched_email": "String",
  "enriched_phone": "String",
  "email_status": "valid|invalid|catch_all",
  "email_quality_score": "String",
  "is_valid_email": Boolean,
  "enrichment_source": "cognism|lusha|apollo",
  "stored_at": DateTime
}
```

## Troubleshooting

### Configuration Error
- Ensure all required API keys are set in `config.py`
- Validate Google credentials JSON format
- Check MongoDB connection string

### API Failures
- Check API key validity and rate limits
- Verify network connectivity
- Review `contact_enrichment.log` for details

### Google Sheets Error
- Verify sheet ID is correct
- Ensure service account has edit permissions
- Check column names match `SHEET_COLUMNS`

## Performance

- **~2-3 seconds per company**: Parallel API calls
- **Batch processing**: Multiple companies in sequence
- **Email verification**: ~200-500ms per email
- **MongoDB writes**: Batched for efficiency

## Production Deployment

1. **Environment Variables**: Use system env vars instead of hardcoding
2. **Error Monitoring**: Integrate with Sentry/DataDog
3. **Rate Limiting**: Add exponential backoff for API calls
4. **Database**: Use MongoDB Atlas for reliability
5. **Scheduling**: Use APScheduler or cloud task runners
6. **Secrets**: Use AWS Secrets Manager or similar

## License

Proprietary - Contact Enrichment System
