"""
Contact Enrichment Pipeline using LangGraph
Finds 5-6 people per company domain and enriches their data
"""

import logging
from typing import TypedDict, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END

from src.config import MAX_CONTACTS_PER_COMPANY, CONTINUE_ON_ERROR
from src.services import (
    GoogleSheetsService, MongoDBService,
    CognismAPI, LushaAPI, ApolloAPI, ZeroBounceAPI
)

logger = logging.getLogger(__name__)


# ============================================================================
# State Definition
# ============================================================================

class PipelineState(TypedDict):
    """LangGraph execution state"""
    companies: list[dict]
    current_company: Optional[dict]
    company_index: int
    found_employees: list[dict]
    enriched_contacts: list[dict]
    errors: list[dict]


# ============================================================================
# Node Functions
# ============================================================================

async def load_companies(state: PipelineState) -> PipelineState:
    """Load unique companies from Google Sheet"""
    try:
        sheets_service = GoogleSheetsService()
        companies = await sheets_service.fetch_companies()
        state['companies'] = companies
        state['company_index'] = 0
        logger.info(f"✓ Loaded {len(companies)} companies")
        return state
    except Exception as e:
        logger.error(f"✗ Failed to load companies: {e}")
        state['errors'].append({'step': 'load_companies', 'error': str(e)})
        return state


async def get_next_company(state: PipelineState) -> PipelineState:
    """Get next company for processing"""
    if state['company_index'] < len(state['companies']):
        state['current_company'] = state['companies'][state['company_index']]
        state['company_index'] += 1
        logger.info(f"Processing: {state['current_company']['company_name']} ({state['current_company']['domain']})")
    return state


async def search_cognism(state: PipelineState) -> PipelineState:
    """Search for employees using Cognism"""
    company = state.get('current_company')
    if not company:
        return state

    try:
        api = CognismAPI()
        employees = await api.search_employees(
            company['company_name'],
            company['domain'],
            limit=MAX_CONTACTS_PER_COMPANY
        )
        state['found_employees'].extend([
            {**emp, 'enrichment_source': 'cognism', **company}
            for emp in employees
        ])
    except Exception as e:
        logger.warning(f"Cognism search failed: {e}")
        if not CONTINUE_ON_ERROR:
            state['errors'].append({'company': company['domain'], 'api': 'cognism', 'error': str(e)})

    return state


async def search_lusha(state: PipelineState) -> PipelineState:
    """Search for employees using Lusha"""
    company = state.get('current_company')
    if not company:
        return state

    try:
        api = LushaAPI()
        employees = await api.search_employees(
            company['company_name'],
            company['domain'],
            limit=MAX_CONTACTS_PER_COMPANY
        )
        state['found_employees'].extend([
            {**emp, 'enrichment_source': 'lusha', **company}
            for emp in employees
        ])
    except Exception as e:
        logger.warning(f"Lusha search failed: {e}")
        if not CONTINUE_ON_ERROR:
            state['errors'].append({'company': company['domain'], 'api': 'lusha', 'error': str(e)})

    return state


async def search_apollo(state: PipelineState) -> PipelineState:
    """Search for employees using Apollo"""
    company = state.get('current_company')
    if not company:
        return state

    try:
        api = ApolloAPI()
        employees = await api.search_employees(
            company['company_name'],
            company['domain'],
            limit=MAX_CONTACTS_PER_COMPANY
        )
        state['found_employees'].extend([
            {**emp, 'enrichment_source': 'apollo', **company}
            for emp in employees
        ])
    except Exception as e:
        logger.warning(f"Apollo search failed: {e}")
        if not CONTINUE_ON_ERROR:
            state['errors'].append({'company': company['domain'], 'api': 'apollo', 'error': str(e)})

    return state


async def deduplicate_employees(state: PipelineState) -> PipelineState:
    """Remove duplicate employees based on email"""
    seen_emails = set()
    unique_employees = []

    for emp in state['found_employees']:
        email = emp.get('email') or emp.get('email_address') or ''
        if email and email.lower() not in seen_emails:
            seen_emails.add(email.lower())
            unique_employees.append(emp)

    # Keep only top N employees per company
    unique_employees = unique_employees[:MAX_CONTACTS_PER_COMPANY]
    state['found_employees'] = unique_employees
    logger.info(f"✓ Deduplicated to {len(unique_employees)} unique employees")

    return state


async def verify_emails(state: PipelineState) -> PipelineState:
    """Verify email addresses using ZeroBounce"""
    api = ZeroBounceAPI()

    for employee in state['found_employees']:
        email = employee.get('email') or employee.get('email_address')
        if not email:
            employee['email_status'] = 'missing'
            employee['is_valid_email'] = False
            continue

        try:
            result = await api.validate_email(email)
            if result:
                employee['email_status'] = result.get('status')
                employee['email_quality_score'] = result.get('sub_status')
                employee['is_valid_email'] = result.get('status') == 'valid'
            else:
                employee['email_status'] = 'unverified'
                employee['is_valid_email'] = False
        except Exception as e:
            logger.warning(f"Email verification failed for {email}: {e}")
            employee['email_status'] = 'error'
            employee['is_valid_email'] = False

    state['enriched_contacts'].extend(state['found_employees'])
    state['found_employees'] = []  # Reset for next company

    return state


async def store_in_mongodb(state: PipelineState) -> PipelineState:
    """Store enriched contacts in MongoDB"""
    if not state['enriched_contacts']:
        return state

    try:
        db = MongoDBService()
        db.store_batch(state['enriched_contacts'])
        db.close()
        logger.info(f"✓ Stored {len(state['enriched_contacts'])} contacts in MongoDB")
    except Exception as e:
        logger.error(f"✗ MongoDB storage failed: {e}")
        if not CONTINUE_ON_ERROR:
            state['errors'].append({'step': 'store_mongodb', 'error': str(e)})

    return state


async def update_google_sheet(state: PipelineState) -> PipelineState:
    """Update Google Sheet with enriched contacts"""
    if not state['enriched_contacts']:
        return state

    try:
        sheets_service = GoogleSheetsService()
        await sheets_service.append_enriched_contacts(state['enriched_contacts'])
        logger.info(f"✓ Updated Google Sheet with {len(state['enriched_contacts'])} rows")
    except Exception as e:
        logger.error(f"✗ Google Sheet update failed: {e}")
        if not CONTINUE_ON_ERROR:
            state['errors'].append({'step': 'update_sheet', 'error': str(e)})

    return state


# ============================================================================
# Conditional Router
# ============================================================================

def should_process_next_company(state: PipelineState) -> str:
    """Route to next company or finish"""
    if state['company_index'] < len(state['companies']):
        return 'process_company'
    return 'finalize'


# ============================================================================
# Graph Builder
# ============================================================================

def build_pipeline_graph():
    """Build LangGraph pipeline"""

    # Initialize state
    initial_state: PipelineState = {
        'companies': [],
        'current_company': None,
        'company_index': 0,
        'found_employees': [],
        'enriched_contacts': [],
        'errors': [],
    }

    # Create graph
    graph = StateGraph(PipelineState)

    # Add nodes
    graph.add_node('load_companies', load_companies)
    graph.add_node('get_company', get_next_company)
    graph.add_node('search_cognism', search_cognism)
    graph.add_node('search_lusha', search_lusha)
    graph.add_node('search_apollo', search_apollo)
    graph.add_node('deduplicate', deduplicate_employees)
    graph.add_node('verify_emails', verify_emails)
    graph.add_node('store_mongodb', store_in_mongodb)
    graph.add_node('update_sheet', update_google_sheet)

    # Add edges
    graph.add_edge('load_companies', 'get_company')
    graph.add_edge('get_company', 'search_cognism')

    # Parallel API calls
    graph.add_edge('search_cognism', 'search_lusha')
    graph.add_edge('search_lusha', 'search_apollo')
    graph.add_edge('search_apollo', 'deduplicate')

    # Email verification and storage
    graph.add_edge('deduplicate', 'verify_emails')
    graph.add_edge('verify_emails', 'store_mongodb')

    # Conditional routing
    graph.add_conditional_edges(
        'store_mongodb',
        should_process_next_company,
        {
            'process_company': 'get_company',
            'finalize': 'update_sheet'
        }
    )

    # Final step
    graph.add_edge('update_sheet', END)

    # Set entry point
    graph.set_entry_point('load_companies')

    return graph.compile(), initial_state


# ============================================================================
# Pipeline Executor
# ============================================================================

class EnrichmentPipeline:
    """Main pipeline orchestrator"""

    def __init__(self):
        self.graph, self.initial_state = build_pipeline_graph()

    async def run(self) -> dict:
        """Execute the enrichment pipeline"""
        logger.info("=" * 60)
        logger.info("Starting Contact Enrichment Pipeline")
        logger.info("=" * 60)

        try:
            state = self.initial_state.copy()
            state = await self.graph.ainvoke(state)

            total = len(state['enriched_contacts'])
            valid = sum(1 for c in state['enriched_contacts'] if c.get('is_valid_email'))

            logger.info("=" * 60)
            logger.info(f"✓ Pipeline completed successfully")
            logger.info(f"  Total contacts enriched: {total}")
            logger.info(f"  Valid emails: {valid}/{total}")
            logger.info(f"  Errors: {len(state['errors'])}")
            logger.info("=" * 60)

            return {
                'success': True,
                'total_contacts': total,
                'valid_emails': valid,
                'enriched_contacts': state['enriched_contacts'],
                'errors': state['errors'],
            }

        except Exception as e:
            logger.error(f"✗ Pipeline failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'errors': self.initial_state['errors'],
            }


# ============================================================================
# Entry Point
# ============================================================================

async def run_pipeline():
    """Execute pipeline"""
    pipeline = EnrichmentPipeline()
    result = await pipeline.run()
    return result


if __name__ == '__main__':
    import asyncio
    asyncio.run(run_pipeline())
