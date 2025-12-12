"""Enrichment API integrations"""

import logging
import httpx
from typing import Optional

from src.config import (
    COGNISM_API_KEY, LUSHA_API_KEY, APOLLO_API_KEY, ZEROBOUNCE_API_KEY, API_TIMEOUT,
    MAX_CONTACTS_PER_COMPANY, CONTACT_LOCATION_COUNTRY, CONTACT_LOCATION_CITY,
    CONTACT_LOCATION_STATE, INCLUDE_DEPARTMENTS, INCLUDE_SENIORITY, INCLUDE_JOB_TITLES,
    REQUIRED_DATA_POINTS, EXCLUDE_DEPARTMENTS, EXCLUDE_SENIORITY, EXCLUDE_JOB_TITLES
)

logger = logging.getLogger(__name__)


def build_contact_filters() -> dict:
    """Build contact filters based on configuration"""
    filters = {
        "include": {},
        "exclude": {}
    }

    # ===== INCLUDE FILTERS =====

    # Location filter
    location_filter = {"country": CONTACT_LOCATION_COUNTRY}
    if CONTACT_LOCATION_CITY:
        location_filter["city"] = CONTACT_LOCATION_CITY
    if CONTACT_LOCATION_STATE:
        location_filter["state"] = CONTACT_LOCATION_STATE
    filters["include"]["locations"] = [location_filter]

    # Departments filter
    if INCLUDE_DEPARTMENTS:
        filters["include"]["departments"] = INCLUDE_DEPARTMENTS

    # Seniority filter
    if INCLUDE_SENIORITY:
        filters["include"]["seniority"] = INCLUDE_SENIORITY

    # Job titles filter
    if INCLUDE_JOB_TITLES:
        filters["include"]["jobTitles"] = INCLUDE_JOB_TITLES

    # Required data points filter
    if REQUIRED_DATA_POINTS:
        filters["include"]["existing_data_points"] = REQUIRED_DATA_POINTS

    # ===== EXCLUDE FILTERS =====

    # Exclude departments
    if EXCLUDE_DEPARTMENTS:
        filters["exclude"]["departments"] = EXCLUDE_DEPARTMENTS

    # Exclude seniority
    if EXCLUDE_SENIORITY:
        filters["exclude"]["seniority"] = EXCLUDE_SENIORITY

    # Exclude job titles
    if EXCLUDE_JOB_TITLES:
        filters["exclude"]["jobTitles"] = EXCLUDE_JOB_TITLES

    # Remove empty exclude object if no exclusions
    if not filters["exclude"]:
        del filters["exclude"]

    return filters


class BaseEnrichmentAPI:
    """Base class for enrichment APIs"""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    async def _request(self, method: str, endpoint: str, **kwargs) -> Optional[dict]:
        """Make HTTP request with error handling"""
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                url = f"{self.base_url}{endpoint}"
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"API request failed: {e}")
            return None


class CognismAPI(BaseEnrichmentAPI):
    """Cognism B2B database API"""

    def __init__(self):
        super().__init__(COGNISM_API_KEY, "https://app.cognism.com/api")

    async def search_employees(self, company_name: str, domain: str, limit: int = 1) -> list[dict]:
        """Search for employees in company using Cognism Search API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            # Build payload with filters based on configuration
            payload = {
                'jobTitles': INCLUDE_JOB_TITLES,
                'excludeJobTitles': EXCLUDE_JOB_TITLES,
                'regions': ['EMEA'],  # France is in EMEA region
                'countries': [CONTACT_LOCATION_COUNTRY],
                'departments': INCLUDE_DEPARTMENTS,
                'emailQuality': {'highPlus': True},  # Require high quality emails
                'account': {
                    'domains': [domain.lower()]
                }
            }

            # Add seniority filter if configured
            if INCLUDE_SENIORITY:
                # Map numeric seniority to Cognism format
                seniority_map = {
                    '5': 'director',
                    '6': 'vp',
                    '7': 'c_level'
                }
                payload['seniorities'] = [seniority_map.get(s, s) for s in INCLUDE_SENIORITY]

            result = await self._request(
                'POST',
                f'/search/contact/search?indexSize={limit}',
                headers=headers,
                json=payload
            )

            if result and isinstance(result, dict):
                people = result.get('contacts', result.get('data', []))
                logger.info(f"✓ Cognism: Found {len(people)} people for {domain}")
                return people
            return []
        except Exception as e:
            logger.warning(f"Cognism search error: {e}")
            return []


class LushaAPI(BaseEnrichmentAPI):
    """Lusha B2B Prospecting API"""

    def __init__(self):
        super().__init__(LUSHA_API_KEY, "https://api.lusha.com/prospecting")

    async def search_employees(self, company_name: str, domain: str, limit: int = 1) -> list[dict]:
        """Search for employees in company using Lusha Prospecting API"""

        try:
            headers = {
                'api_key': self.api_key,
                'Content-Type': 'application/json'
            }

            # Build contact filters using configuration
            contact_filters = build_contact_filters()

            payload = {
                "pages": {
                    "page": 0,
                    "size": limit
                },
                "filters": {
                    "contacts": contact_filters,
                    "companies": {
                        "include": {
                            "fqdns": [domain.lower()]
                        }
                    }
                }
            }

            result = await self._request(
                'POST',
                '/contact/search',
                headers=headers,
                json=payload
            )

            if result and result.get('data'):
                people = result['data']
                logger.info(f"✓ Lusha: Found {len(people)} people for {domain}")
                return people
            return []
        except Exception as e:
            logger.warning(f"Lusha search error: {e}")
            return []


class ApolloAPI(BaseEnrichmentAPI):
    """Apollo B2B database API"""

    def __init__(self):
        super().__init__(APOLLO_API_KEY, "https://api.apollo.io/api/v1")

    async def search_employees(self, company_name: str, domain: str, limit: int = 1) -> list[dict]:
        """Search for employees in company using Apollo People API Search"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key
            }

            # Build payload with filters based on configuration
            payload = {
                'page': 1,
                'per_page': limit,
                'person_titles': INCLUDE_JOB_TITLES,
                'q_organization_domains': domain.lower(),
            }

            # Add location filter
            if CONTACT_LOCATION_COUNTRY:
                payload['person_locations'] = [CONTACT_LOCATION_COUNTRY]

            # Add seniority filter
            if INCLUDE_SENIORITY:
                # Map numeric seniority to Apollo format
                seniority_map = {
                    '4': 'manager',
                    '5': 'director',
                    '6': 'vp',
                    '7': 'cxo'
                }
                payload['person_seniorities'] = [seniority_map.get(s, s) for s in INCLUDE_SENIORITY]

            # Add contact email requirement
            payload['contact_email_status'] = ['verified', 'guessed', 'unavailable']

            result = await self._request(
                'POST',
                '/mixed_people/api_search',
                headers=headers,
                json=payload
            )

            if result and isinstance(result, dict):
                people = result.get('people', result.get('contacts', []))
                # Filter out excluded job titles on client side
                filtered_people = []
                for person in people:
                    job_title = person.get('title', '').lower()
                    if not any(excluded.lower() in job_title for excluded in EXCLUDE_JOB_TITLES):
                        filtered_people.append(person)

                logger.info(f"✓ Apollo: Found {len(filtered_people)} people for {domain} (filtered from {len(people)})")
                return filtered_people
            return []
        except Exception as e:
            logger.warning(f"Apollo search error: {e}")
            return []


class ZeroBounceAPI(BaseEnrichmentAPI):
    """ZeroBounce email verification API"""

    def __init__(self):
        super().__init__(ZEROBOUNCE_API_KEY, "https://api.zerobounce.net/v2")

    async def validate_email(self, email: str) -> Optional[dict]:
        """Validate email address"""
        try:
            params = {
                'api_key': self.api_key,
                'email': email,
            }

            result = await self._request(
                'GET',
                '/validate',
                params=params
            )

            if result:
                logger.info(f"✓ ZeroBounce: Validated {email}")
                return result
            return None
        except Exception as e:
            logger.warning(f"ZeroBounce validation error: {e}")
            return None
