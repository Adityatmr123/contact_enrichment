#!/usr/bin/env python
"""
Entry point for Contact Enrichment Pipeline
Run this script to start the pipeline
"""

import sys
from src.main import main
import asyncio


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
