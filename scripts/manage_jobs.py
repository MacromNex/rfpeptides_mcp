#!/usr/bin/env python
"""Manage RFpeptides backbone generation jobs.

Provides commands for job monitoring, result retrieval, and job control.

Usage:
    python manage_jobs.py status <job_id>
    python manage_jobs.py result <job_id>
    python manage_jobs.py log <job_id>
    python manage_jobs.py list
    python manage_jobs.py cancel <job_id>
    python manage_jobs.py resubmit <job_id>
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(MCP_ROOT))

from src.jobs.manager import job_manager


def cmd_status(args):
    """Get job status."""
    result = job_manager.get_job_status(args.job_id)
    print(json.dumps(result, indent=2))


def cmd_result(args):
    """Get job results."""
    result = job_manager.get_job_result(args.job_id)
    print(json.dumps(result, indent=2))

    if result.get("status") == "success":
        print("\nOutput files:")
        for pdb in result.get("pdb_files", []):
            print(f"  {pdb}")


def cmd_log(args):
    """Get job log."""
    result = job_manager.get_job_log(args.job_id, tail=args.tail)

    if result.get("status") == "error":
        print(f"Error: {result['error']}")
        return

    print(f"Log for job {args.job_id} ({result['total_lines']} lines total):")
    print("-" * 60)
    for line in result.get("log_lines", []):
        print(line, end="")


def cmd_list(args):
    """List all jobs."""
    result = job_manager.list_jobs(status=args.status)

    if not result.get("jobs"):
        print("No jobs found.")
        return

    print(f"{'JOB ID':<10} {'NAME':<30} {'STATUS':<12} {'SUBMITTED':<20}")
    print("-" * 80)

    for job in result["jobs"]:
        submitted = job.get("submitted_at", "")[:19].replace("T", " ")
        print(
            f"{job['job_id']:<10} "
            f"{(job.get('job_name') or '')[:30]:<30} "
            f"{job['status']:<12} "
            f"{submitted:<20}"
        )

    print(f"\nTotal: {result['total']} jobs")


def cmd_queue(args):
    """Get queue info."""
    result = job_manager.get_queue_info()
    print(json.dumps(result, indent=2))


def cmd_cancel(args):
    """Cancel a job."""
    result = job_manager.cancel_job(args.job_id)
    print(json.dumps(result, indent=2))


def cmd_resubmit(args):
    """Resubmit a failed job."""
    result = job_manager.resubmit_job(args.job_id)
    print(json.dumps(result, indent=2))


def cmd_recover(args):
    """Recover interrupted jobs."""
    result = job_manager.recover_jobs()
    print(json.dumps(result, indent=2))

    if result.get("recovered"):
        print(f"\nRecovered jobs will now be processed.")
        print("Use 'python manage_jobs.py list' to check status.")


def main():
    parser = argparse.ArgumentParser(
        description="Manage RFpeptides backbone generation jobs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Status command
    status_parser = subparsers.add_parser("status", help="Get job status")
    status_parser.add_argument("job_id", help="Job ID")
    status_parser.set_defaults(func=cmd_status)

    # Result command
    result_parser = subparsers.add_parser("result", help="Get job results")
    result_parser.add_argument("job_id", help="Job ID")
    result_parser.set_defaults(func=cmd_result)

    # Log command
    log_parser = subparsers.add_parser("log", help="Get job log")
    log_parser.add_argument("job_id", help="Job ID")
    log_parser.add_argument("--tail", type=int, default=50, help="Number of lines (default: 50)")
    log_parser.set_defaults(func=cmd_log)

    # List command
    list_parser = subparsers.add_parser("list", help="List all jobs")
    list_parser.add_argument(
        "--status",
        choices=["pending", "running", "completed", "failed", "cancelled"],
        help="Filter by status",
    )
    list_parser.set_defaults(func=cmd_list)

    # Queue command
    queue_parser = subparsers.add_parser("queue", help="Get queue info")
    queue_parser.set_defaults(func=cmd_queue)

    # Cancel command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a job")
    cancel_parser.add_argument("job_id", help="Job ID")
    cancel_parser.set_defaults(func=cmd_cancel)

    # Resubmit command
    resubmit_parser = subparsers.add_parser("resubmit", help="Resubmit a failed job")
    resubmit_parser.add_argument("job_id", help="Job ID")
    resubmit_parser.set_defaults(func=cmd_resubmit)

    # Recover command
    recover_parser = subparsers.add_parser("recover", help="Recover interrupted jobs")
    recover_parser.set_defaults(func=cmd_recover)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
