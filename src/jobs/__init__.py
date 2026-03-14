"""Job management for RFpeptides MCP tools with FIFO queue support."""

import sys
from pathlib import Path

# Add jobs directory to path for standalone execution
_jobs_dir = Path(__file__).parent
if str(_jobs_dir) not in sys.path:
    sys.path.insert(0, str(_jobs_dir))

from manager import JobManager, JobStatus, job_manager

__all__ = ['JobManager', 'JobStatus', 'job_manager']
