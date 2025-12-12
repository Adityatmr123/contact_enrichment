"""Google Sheets integration with async support"""

import logging
import gspread_asyncio
from oauth2client.service_account import ServiceAccountCredentials

from src.config import GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_PATH, GOOGLE_SCOPES, SHEET_COLUMNS, CONTINUE_ON_ERROR

logger = logging.getLogger(__name__)


def get_creds():
    """Get Google Sheets service account credentials"""
    scope = GOOGLE_SCOPES
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_PATH, scope)
    return creds


class GoogleSheetsService:
    """Google Sheets integration for reading and updating contacts"""

    def __init__(self):
        self.agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        self.client = None
        logger.info("✓ Google Sheets client manager initialized")

    async def _get_client(self):
        """Get authenticated async gspread client"""
        if not self.client:
            try:
                self.client = await self.agcm.authorize()
                logger.info("✓ Google Sheets authenticated")
            except Exception as e:
                logger.error(f"✗ Google Sheets auth failed: {e}")
                raise
        return self.client

    async def fetch_companies(self) -> list[dict]:
        """Fetch unique companies from sheet"""
        try:
            client = await self._get_client()
            sheet = await client.open_by_key(GOOGLE_SHEET_ID)
            worksheet = sheet.get_worksheet(0)
            records = await worksheet.get_all_records()

            # Get unique companies by domain
            companies = {}
            for record in records:
                domain = record.get(SHEET_COLUMNS['domain'], '').strip()
                if domain and domain not in companies:
                    companies[domain] = {
                        'company_name': record.get(SHEET_COLUMNS['company_name'], ''),
                        'domain': domain,
                    }

            logger.info(f"✓ Fetched {len(companies)} unique companies")
            return list(companies.values())
        except Exception as e:
            logger.error(f"✗ Error fetching companies: {e}")
            raise

    async def append_enriched_contacts(self, contacts: list[dict]) -> bool:
        """Append enriched contacts to sheet"""
        try:
            client = await self._get_client()
            sheet = await client.open_by_key(GOOGLE_SHEET_ID)
            worksheet = sheet.get_worksheet(0)

            # Prepare rows for insertion
            rows = []
            for contact in contacts:
                row = [
                    contact.get('company_name', ''),
                    contact.get('domain', ''),
                    contact.get('name', ''),
                    contact.get('enriched_email', ''),
                    contact.get('enriched_phone', ''),
                    contact.get('linkedin_url', ''),
                    contact.get('job_title', ''),
                    contact.get('department', ''),
                    contact.get('seniority', ''),
                    contact.get('enrichment_source', ''),
                    contact.get('email_status', ''),
                    contact.get('email_quality_score', ''),
                    'processed',
                ]
                rows.append(row)

            if rows:
                await worksheet.append_rows(rows)
                logger.info(f"✓ Appended {len(rows)} rows to Google Sheet")
                return True

            return True
        except Exception as e:
            logger.error(f"✗ Error updating sheet: {e}")
            if not CONTINUE_ON_ERROR:
                raise
            return False
