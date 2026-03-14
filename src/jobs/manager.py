"""Job management for RFpeptides backbone generation with FIFO queue support."""

import uuid
import json
import subprocess
import threading
import queue
import os
import fcntl
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Resolve paths relative to this file's location
_MODULE_DIR = Path(__file__).parent.absolute()
_SRC_DIR = _MODULE_DIR.parent
_MCP_ROOT = _SRC_DIR.parent

# RFdiffusion directory - can be overridden via environment variable (e.g., in Docker)
_RFDIFF_DIR = Path(os.environ.get("RFPEPTIDES_RFDIFF_DIR", str(_MCP_ROOT / "repo" / "rfd_macro")))
_ENV_PATH = _MCP_ROOT / "env_rfpeptides"

# Default mamba path - can be overridden via environment variable
_DEFAULT_MAMBA = "/home/xux/miniforge3/bin/mamba"
MAMBA_PATH = os.environ.get("RFPEPTIDES_MAMBA_PATH", _DEFAULT_MAMBA)

# Docker mode: skip mamba if not available
_USE_MAMBA = Path(MAMBA_PATH).exists() and _ENV_PATH.exists()


class JobManager:
    """Manages asynchronous job execution with FIFO queue for RFpeptides backbone generation.

    Only one job runs at a time (GPU-intensive tasks), others wait in queue.
    """

    def __init__(self, jobs_dir: Path = None, auto_recover: bool = False):
        self.jobs_dir = jobs_dir or _MCP_ROOT / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

        # Job queue for FIFO execution
        self._job_queue: queue.Queue = queue.Queue()
        self._current_job: Optional[str] = None
        self._running_process: Optional[subprocess.Popen] = None

        # Lock for thread-safe operations
        self._lock = threading.Lock()

        # Start the queue worker thread
        self._worker_thread = threading.Thread(target=self._queue_worker, daemon=True)
        self._worker_thread.start()

        # Only recover pending jobs if explicitly requested
        # This prevents duplicate processing when multiple scripts import job_manager
        if auto_recover:
            self._recover_pending_jobs()

    def _recover_pending_jobs(self):
        """Recover and re-queue pending/running jobs from previous sessions.

        Uses file locking to prevent multiple processes from recovering simultaneously.
        """
        lock_file = self.jobs_dir / ".recovery.lock"

        try:
            # Try to acquire exclusive lock (non-blocking)
            lock_fd = open(lock_file, 'w')
            try:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                # Another process is recovering, skip
                lock_fd.close()
                logger.debug("Job recovery already in progress by another process")
                return

            # Collect jobs to recover, sorted by submission time (FIFO)
            jobs_to_recover = []
            for job_dir in self.jobs_dir.iterdir():
                if job_dir.is_dir() and not job_dir.name.startswith('.'):
                    metadata = self._load_metadata(job_dir.name)
                    if metadata and metadata["status"] in [JobStatus.PENDING.value, JobStatus.RUNNING.value]:
                        jobs_to_recover.append(metadata)

            # Sort by submission time to maintain FIFO order
            jobs_to_recover.sort(key=lambda x: x.get("submitted_at", ""))

            for metadata in jobs_to_recover:
                job_id = metadata["job_id"]
                job_dir = self.jobs_dir / job_id

                # Reset status to pending and clear timing info
                was_running = metadata["status"] == JobStatus.RUNNING.value
                metadata["status"] = JobStatus.PENDING.value
                metadata["started_at"] = None
                metadata["completed_at"] = None
                metadata["error"] = None
                if was_running:
                    metadata["recovered_from"] = "running"
                self._save_metadata(job_id, metadata)

                # Re-queue the job
                self._job_queue.put((job_id, metadata["config"], job_dir))
                logger.info(f"Recovered job {job_id} ({metadata.get('job_name', 'unnamed')})")

            if jobs_to_recover:
                logger.info(f"Recovered {len(jobs_to_recover)} job(s) from previous session")

            # Release lock
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()

        except Exception as e:
            logger.warning(f"Error recovering jobs: {e}")

    def recover_jobs(self) -> Dict[str, Any]:
        """Manually recover and re-queue pending/running jobs.

        Call this explicitly to restart jobs that were interrupted (e.g., system restart).

        Returns:
            Dict with status and list of recovered job IDs.
        """
        # Get pending/running jobs before recovery
        pending_before = []
        for job_dir in self.jobs_dir.iterdir():
            if job_dir.is_dir() and not job_dir.name.startswith('.'):
                metadata = self._load_metadata(job_dir.name)
                if metadata and metadata["status"] in [JobStatus.PENDING.value, JobStatus.RUNNING.value]:
                    pending_before.append(metadata["job_id"])

        if not pending_before:
            return {"status": "success", "message": "No jobs to recover", "recovered": []}

        self._recover_pending_jobs()

        return {
            "status": "success",
            "message": f"Recovered {len(pending_before)} job(s)",
            "recovered": pending_before
        }

    def _queue_worker(self):
        """Worker thread that processes jobs from the queue one at a time (FIFO)."""
        while True:
            try:
                # Block until a job is available
                job_id, config, job_dir = self._job_queue.get(block=True)

                with self._lock:
                    self._current_job = job_id

                # Execute the job
                self._execute_job(job_id, config, job_dir)

                with self._lock:
                    self._current_job = None
                    self._running_process = None

                self._job_queue.task_done()

            except Exception as e:
                logger.error(f"Queue worker error: {e}")

    def submit_job(
        self,
        config: Dict[str, Any],
        job_name: str = None
    ) -> Dict[str, Any]:
        """Submit a new RFpeptides job to the FIFO queue.

        Args:
            config: RFdiffusion configuration dictionary containing:
                - output_prefix: Path prefix for output files
                - num_designs: Number of designs to generate
                - contigs: Contig specification string
                - cyclic: Whether to generate cyclic peptides
                - cyc_chains: Chain(s) to make cyclic
                - diffusion_steps: Number of diffusion timesteps
                - input_pdb: Optional target PDB file
                - hotspot_res: Optional hotspot residue string
            job_name: Optional name for the job

        Returns:
            Dict with job_id, status, and queue position
        """
        job_id = str(uuid.uuid4())[:8]
        job_dir = self.jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # Update output prefix to use job directory
        config = dict(config)  # Make a copy
        original_prefix = config.get("output_prefix", "design")
        output_name = Path(original_prefix).name
        config["output_prefix"] = str(job_dir / output_name)

        # Save job metadata
        metadata = {
            "job_id": job_id,
            "job_name": job_name or f"job_{job_id}",
            "config": config,
            "status": JobStatus.PENDING.value,
            "submitted_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None
        }

        self._save_metadata(job_id, metadata)

        # Add job to queue
        self._job_queue.put((job_id, config, job_dir))

        # Get queue position
        queue_position = self._job_queue.qsize()

        return {
            "status": "submitted",
            "job_id": job_id,
            "queue_position": queue_position,
            "message": f"Job queued (position {queue_position}). Use get_job_status('{job_id}') to check progress."
        }

    def _build_command(self, config: Dict[str, Any]) -> list[str]:
        """Build the RFdiffusion command from configuration."""
        if _USE_MAMBA:
            cmd = [MAMBA_PATH, "run", "-p", str(_ENV_PATH), "python"]
        else:
            cmd = ["python"]
        cmd += [
            "scripts/run_inference.py",
            f"--config-name={config.get('config_name', 'base')}",
            f"inference.output_prefix={config['output_prefix']}",
            f"inference.num_designs={config['num_designs']}",
            f"contigmap.contigs=[{config['contigs']}]",
            f"inference.cyclic={config.get('cyclic', True)}",
            f"inference.cyc_chains={config['cyc_chains']!r}",
            f"diffuser.T={config.get('diffusion_steps', 50)}",
        ]

        if config.get("input_pdb"):
            cmd.append(f"inference.input_pdb={config['input_pdb']}")

        if config.get("hotspot_res"):
            cmd.append(f"ppi.hotspot_res=[{config['hotspot_res']}]")

        return cmd

    def _execute_job(self, job_id: str, config: Dict, job_dir: Path):
        """Execute a job (called by queue worker)."""
        metadata = self._load_metadata(job_id)

        # Check if job was cancelled while waiting
        if metadata["status"] == JobStatus.CANCELLED.value:
            logger.info(f"Skipping cancelled job {job_id}")
            return

        metadata["status"] = JobStatus.RUNNING.value
        metadata["started_at"] = datetime.now().isoformat()
        self._save_metadata(job_id, metadata)

        try:
            # Validate paths
            if not _RFDIFF_DIR.exists():
                raise FileNotFoundError(
                    f"RFdiffusion directory not found: {_RFDIFF_DIR}. "
                    "Set RFPEPTIDES_RFDIFF_DIR or ensure repo is properly linked."
                )
            if _USE_MAMBA and not _ENV_PATH.exists():
                raise FileNotFoundError(
                    f"RFpeptides environment not found: {_ENV_PATH}"
                )

            # Build command
            cmd = self._build_command(config)
            cmd_str = " ".join(cmd)

            logger.info(f"Running job {job_id}: {cmd_str}")

            # Set up environment with CUDA device selection
            env = os.environ.copy()
            device = config.get("device")
            if device is not None:
                env["CUDA_VISIBLE_DEVICES"] = str(device)
                cmd_str = f"CUDA_VISIBLE_DEVICES={device} " + cmd_str

            # Run RFdiffusion
            log_file = job_dir / "job.log"
            with open(log_file, 'w') as log:
                log.write(f"Command: {cmd_str}\n")
                log.write(f"Working directory: {_RFDIFF_DIR}\n")
                if device is not None:
                    log.write(f"CUDA device: {device}\n")
                log.write("=" * 60 + "\n")
                log.flush()

                process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    cwd=str(_RFDIFF_DIR),
                    env=env,
                )

                with self._lock:
                    self._running_process = process

                process.wait()

            # Collect output files
            output_prefix = Path(config["output_prefix"]).name
            pdb_files = sorted(job_dir.glob(f"{output_prefix}*.pdb"))
            trb_files = sorted(job_dir.glob(f"{output_prefix}*.trb"))

            # Update status
            if process.returncode == 0 and pdb_files:
                metadata["status"] = JobStatus.COMPLETED.value
                # Save result info
                result = {
                    "output_dir": str(job_dir),
                    "pdb_files": [str(p) for p in pdb_files],
                    "trb_files": [str(p) for p in trb_files],
                    "num_generated": len(pdb_files),
                    "success": True
                }
                result_file = job_dir / "result.json"
                with open(result_file, 'w') as f:
                    json.dump(result, f, indent=2)
            else:
                metadata["status"] = JobStatus.FAILED.value
                if process.returncode != 0:
                    metadata["error"] = f"Process exited with code {process.returncode}"
                else:
                    metadata["error"] = "No output PDB files generated"

        except Exception as e:
            metadata["status"] = JobStatus.FAILED.value
            metadata["error"] = str(e)
            logger.error(f"Job {job_id} failed: {e}")

        finally:
            metadata["completed_at"] = datetime.now().isoformat()
            self._save_metadata(job_id, metadata)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a submitted job."""
        metadata = self._load_metadata(job_id)
        if not metadata:
            return {"status": "error", "error": f"Job {job_id} not found"}

        result = {
            "job_id": job_id,
            "job_name": metadata.get("job_name"),
            "status": metadata["status"],
            "submitted_at": metadata.get("submitted_at"),
            "started_at": metadata.get("started_at"),
            "completed_at": metadata.get("completed_at")
        }

        # Add queue info for pending jobs
        if metadata["status"] == JobStatus.PENDING.value:
            result["queue_position"] = self._get_queue_position(job_id)

        if metadata["status"] == JobStatus.FAILED.value:
            result["error"] = metadata.get("error")

        return result

    def _get_queue_position(self, job_id: str) -> int:
        """Get position of a job in the queue."""
        position = 1
        pending_jobs = self.list_jobs(status=JobStatus.PENDING.value)
        for job in pending_jobs.get("jobs", []):
            if job["job_id"] == job_id:
                return position
            position += 1
        return 0

    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """Get results of a completed job."""
        metadata = self._load_metadata(job_id)
        if not metadata:
            return {"status": "error", "error": f"Job {job_id} not found"}

        if metadata["status"] != JobStatus.COMPLETED.value:
            return {
                "status": "error",
                "error": f"Job not completed. Current status: {metadata['status']}"
            }

        # Load result
        job_dir = self.jobs_dir / job_id
        result_file = job_dir / "result.json"

        if result_file.exists():
            with open(result_file) as f:
                result = json.load(f)
            return {"status": "success", "job_id": job_id, **result}
        else:
            # Return basic info if result file not found
            return {
                "status": "success",
                "job_id": job_id,
                "output_dir": str(job_dir)
            }

    def get_job_log(self, job_id: str, tail: int = 50) -> Dict[str, Any]:
        """Get log output from a job."""
        job_dir = self.jobs_dir / job_id
        log_file = job_dir / "job.log"

        if not log_file.exists():
            return {"status": "error", "error": f"Log not found for job {job_id}"}

        with open(log_file) as f:
            lines = f.readlines()

        return {
            "status": "success",
            "job_id": job_id,
            "log_lines": lines[-tail:] if tail > 0 else lines,
            "total_lines": len(lines)
        }

    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a pending or running job."""
        metadata = self._load_metadata(job_id)
        if not metadata:
            return {"status": "error", "error": f"Job {job_id} not found"}

        if metadata["status"] == JobStatus.COMPLETED.value:
            return {"status": "error", "error": "Cannot cancel completed job"}

        if metadata["status"] == JobStatus.CANCELLED.value:
            return {"status": "error", "error": "Job already cancelled"}

        # If running, terminate the process
        with self._lock:
            if self._current_job == job_id and self._running_process:
                self._running_process.terminate()

        # Update metadata
        metadata["status"] = JobStatus.CANCELLED.value
        metadata["completed_at"] = datetime.now().isoformat()
        self._save_metadata(job_id, metadata)

        return {"status": "success", "message": f"Job {job_id} cancelled"}

    def resubmit_job(self, job_id: str) -> Dict[str, Any]:
        """Resubmit a failed or cancelled job.

        Args:
            job_id: The job ID to resubmit

        Returns:
            Dict with new job submission info or error
        """
        metadata = self._load_metadata(job_id)
        if not metadata:
            return {"status": "error", "error": f"Job {job_id} not found"}

        # Only allow resubmit for failed or cancelled jobs
        if metadata["status"] not in [JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
            return {
                "status": "error",
                "error": f"Can only resubmit failed or cancelled jobs. Current status: {metadata['status']}"
            }

        # Get the original config
        config = metadata.get("config")
        job_name = metadata.get("job_name")

        if not config:
            return {
                "status": "error",
                "error": "Cannot resubmit: missing config in job metadata"
            }

        # Submit as a new job with reference to original
        new_job_name = f"{job_name}_retry" if job_name else None
        result = self.submit_job(config=config, job_name=new_job_name)

        # Add reference to original job
        if result.get("status") == "submitted":
            new_job_id = result["job_id"]
            new_metadata = self._load_metadata(new_job_id)
            if new_metadata:
                new_metadata["resubmitted_from"] = job_id
                self._save_metadata(new_job_id, new_metadata)
            result["original_job_id"] = job_id

        return result

    def list_jobs(self, status: Optional[str] = None) -> Dict[str, Any]:
        """List all jobs, optionally filtered by status."""
        jobs = []
        for job_dir in sorted(self.jobs_dir.iterdir(), key=lambda x: x.stat().st_mtime):
            if job_dir.is_dir():
                metadata = self._load_metadata(job_dir.name)
                if metadata:
                    if status is None or metadata["status"] == status:
                        jobs.append({
                            "job_id": metadata["job_id"],
                            "job_name": metadata.get("job_name"),
                            "status": metadata["status"],
                            "submitted_at": metadata.get("submitted_at"),
                            "started_at": metadata.get("started_at"),
                            "completed_at": metadata.get("completed_at")
                        })

        return {"status": "success", "jobs": jobs, "total": len(jobs)}

    def get_queue_info(self) -> Dict[str, Any]:
        """Get current queue status."""
        pending = self.list_jobs(status=JobStatus.PENDING.value)
        running = self.list_jobs(status=JobStatus.RUNNING.value)

        return {
            "status": "success",
            "queue_size": self._job_queue.qsize(),
            "current_job": self._current_job,
            "pending_jobs": pending.get("total", 0),
            "running_jobs": running.get("total", 0)
        }

    def _save_metadata(self, job_id: str, metadata: Dict):
        """Save job metadata to disk atomically."""
        meta_file = self.jobs_dir / job_id / "metadata.json"
        meta_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file first, then rename (atomic on POSIX)
        temp_file = meta_file.with_suffix('.json.tmp')
        with open(temp_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        temp_file.rename(meta_file)

    def _load_metadata(self, job_id: str) -> Optional[Dict]:
        """Load job metadata from disk."""
        meta_file = self.jobs_dir / job_id / "metadata.json"
        if meta_file.exists():
            try:
                with open(meta_file) as f:
                    content = f.read()
                    if content.strip():
                        return json.loads(content)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load metadata for {job_id}: {e}")
        return None


# Global job manager instance
job_manager = JobManager()
