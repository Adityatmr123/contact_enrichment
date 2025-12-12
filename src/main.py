"""
Entry point for Contact Enrichment Pipeline
Setup logging and execute pipeline
"""

import asyncio
import logging
import sys

import config
from src.utils import setup_logging
from src.pipeline import run_pipeline


async def main():
    """Main entry point"""
    logger = setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 70)
    logger.info("CONTACT ENRICHMENT PIPELINE")
    logger.info("=" * 70)

    try:
        # Run pipeline
        result = await run_pipeline()

        # Print summary
        if result['success']:
            logger.info("\n" + "=" * 70)
            logger.info("EXECUTION SUMMARY")
            logger.info("=" * 70)
            logger.info(f"Status: ✓ SUCCESS")
            logger.info(f"Total Contacts Enriched: {result.get('total_contacts', 0)}")
            logger.info(f"Valid Emails: {result.get('valid_emails', 0)}")
            logger.info(f"Errors: {result.get('errors', [])}")
            logger.info("=" * 70)
            return 0
        else:
            logger.error("\n" + "=" * 70)
            logger.error("EXECUTION FAILED")
            logger.error("=" * 70)
            logger.error(f"Error: {result.get('error')}")
            logger.error("=" * 70)
            return 1

    except Exception as e:
        logger.error(f"\n✗ Unexpected Error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
