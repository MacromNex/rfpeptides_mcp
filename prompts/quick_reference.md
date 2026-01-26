# RFpeptides Quick Reference

## Common Commands

### Design Binders (Basic)
```
submit_cyclic_binder(
    target_pdb="/path/to/target.pdb",
    binder_length=12,
    binder_length_max=16,
    num_designs=50
)
```

### Design Binders (With Hotspots)
```
submit_cyclic_binder_with_hotspots(
    target_pdb="/path/to/target.pdb",
    hotspot_residues=[46, 48, 49, 50, 60, 63],
    binder_length=13,
    binder_length_max=18,
    num_designs=50
)
```

### Generate Backbones (No Target)
```
submit_cyclic_backbone(
    peptide_length=10,
    peptide_length_max=12,
    num_designs=100
)
```

### Check Job Status
```
get_job_status(job_id="abc123")
```

### Get Results
```
get_job_result(job_id="abc123")
```

### View Logs
```
get_job_log(job_id="abc123", tail=50)
```

### List All Jobs
```
list_jobs()
list_jobs(status="completed")
list_jobs(status="failed")
```

### Queue Info
```
get_queue_info()
```

### Cancel Job
```
cancel_job(job_id="abc123")
```

### Retry Failed Job
```
resubmit_job(job_id="abc123")
```

### Validate PDB
```
validate_pdb_file(file_path="/path/to/target.pdb")
```

### Server Info
```
get_server_info()
```

---

## Parameter Quick Guide

| Use Case | Length | Designs | Notes |
|----------|--------|---------|-------|
| Quick test | 12-14 | 5-10 | Fast iteration |
| Standard | 12-16 | 50 | Good coverage |
| Thorough | 12-18 | 100-500 | Better diversity |
| Production | 12-20 | 1000+ | Comprehensive |

---

## Job States

| Status | Meaning |
|--------|---------|
| `pending` | In queue, waiting |
| `running` | Currently executing |
| `completed` | Finished successfully |
| `failed` | Error occurred |
| `cancelled` | User cancelled |

---

## Output Files

Each job creates:
- `{prefix}_0.pdb`, `{prefix}_1.pdb`, ... - Generated structures
- `{prefix}_0.trb`, `{prefix}_1.trb`, ... - Trajectory metadata
- `job.log` - Execution log
- `metadata.json` - Job configuration
- `result.json` - Output summary
