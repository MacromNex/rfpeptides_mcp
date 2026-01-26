# RFpeptides Binder Design Workflow Prompts

This document contains prompts for running cyclic peptide binder design end-to-end using the RFpeptides MCP server.

---

## Quick Start Prompt

Use this prompt for a simple binder design task:

```
Design a cyclic peptide binder for the target protein in [PATH_TO_PDB].

Steps:
1. First validate the PDB file using validate_pdb_file
2. Submit a binder design job with submit_cyclic_binder (12-16 residues, 10 designs)
3. Monitor the job with get_job_status until completed
4. Retrieve results with get_job_result
```

---

## Detailed Workflow Prompts

### Prompt 1: Target Validation

```
I want to design cyclic peptide binders for the target protein at:
[TARGET_PDB_PATH]

Please:
1. Use validate_pdb_file to check the structure
2. Report which chains are available and their residue counts
3. Suggest appropriate parameters for binder design based on the target size
```

**Expected tool calls:**
- `validate_pdb_file(file_path="[TARGET_PDB_PATH]")`

---

### Prompt 2: Basic Binder Design (No Hotspots)

```
Design cyclic peptide binders for the target protein:
- Target PDB: [TARGET_PDB_PATH]
- Target chain: A
- Target residue range: 1-180 (or auto-detect)
- Binder length: 12-16 residues
- Number of designs: 50

Submit the job and report the job ID for tracking.
```

**Expected tool calls:**
- `submit_cyclic_binder(target_pdb="[PATH]", binder_length=12, binder_length_max=16, num_designs=50, target_chain="A")`

---

### Prompt 3: Epitope-Specific Binder Design (With Hotspots)

```
Design cyclic peptide binders targeting specific epitope residues:
- Target PDB: [TARGET_PDB_PATH]
- Target chain: A
- Hotspot residues: [46, 48, 49, 50, 60, 63]
- Binder length: 13-18 residues
- Number of designs: 50

These hotspots correspond to the LIR-docking site on GABARAP.
Submit the job with epitope-specific targeting.
```

**Expected tool calls:**
- `submit_cyclic_binder_with_hotspots(target_pdb="[PATH]", hotspot_residues=[46,48,49,50,60,63], binder_length=13, binder_length_max=18, num_designs=50)`

---

### Prompt 4: Job Monitoring

```
Check the status of my RFpeptides job: [JOB_ID]

If it's still running:
- Show the current queue position or runtime
- Display the last 20 lines of the log

If it's completed:
- Report the number of designs generated
- List the output PDB files
```

**Expected tool calls:**
- `get_job_status(job_id="[JOB_ID]")`
- `get_job_log(job_id="[JOB_ID]", tail=20)` (if running)
- `get_job_result(job_id="[JOB_ID]")` (if completed)

---

### Prompt 5: Results Retrieval

```
My binder design job [JOB_ID] has completed.

Please:
1. Get the full results including all output files
2. Summarize what was generated (number of PDBs, location)
3. Suggest next steps for the designed binders
```

**Expected tool calls:**
- `get_job_result(job_id="[JOB_ID]")`

---

## Complete End-to-End Prompt

Use this comprehensive prompt for a full workflow:

```
I want to design cyclic peptide binders for [TARGET_NAME].

Target information:
- PDB file: [TARGET_PDB_PATH]
- Chain: [CHAIN_ID, default A]
- Residue range: [START-END, or "auto-detect"]
- Hotspot residues: [LIST or "none"]

Design parameters:
- Binder length: [MIN]-[MAX] residues
- Number of designs: [N]
- Diffusion steps: [50 default]

Please:
1. Validate the target PDB structure
2. Submit the appropriate binder design job (with/without hotspots)
3. Report the job ID and estimated queue position
4. Provide instructions for checking job status

After the job completes, I'll ask you to retrieve the results.
```

---

## Example: GABARAP Binder Design

### Step 1: Validate and Submit

```
Design cyclic peptide binders for GABARAP (autophagy receptor).

Target: examples/01_diverse_binding_sites/pdbs/3D32.pdb
Chain: A
Residue range: 1-117

I want two types of binders:
1. General binders (no hotspots) - 13-18 residues, 25 designs
2. LIR-docking site binders with hotspots [46, 48, 49, 50, 60, 63] - 13-18 residues, 25 designs

Please validate the PDB first, then submit both jobs.
```

### Step 2: Monitor Progress

```
Check the status of my GABARAP binder design jobs:
- Job 1 (general): [JOB_ID_1]
- Job 2 (hotspots): [JOB_ID_2]

Show queue info and any running job logs.
```

### Step 3: Retrieve Results

```
Both GABARAP binder jobs have completed:
- Job 1: [JOB_ID_1]
- Job 2: [JOB_ID_2]

Please:
1. Get results from both jobs
2. Compare the number of successful designs
3. List all generated PDB files
4. Suggest next steps (e.g., sequence design with LigandMPNN, structure validation with AfCycDesign)
```

---

## Example: MCL1 Binder with Hotspots

```
Design cyclic peptide inhibitors for MCL1 (anti-apoptotic protein).

Target: examples/01_diverse_binding_sites/pdbs/2PQK.pdb
Chain: A
Residue range: 1-180

Hotspot residues (BH3-binding groove):
- Leu267 (A267)
- Leu270 (A270)
- Gly271 (A271)
- Val274 (A274)
- Met231 (A231)
- Phe228 (A228)

Design parameters:
- Binder length: 12-16 residues
- Number of designs: 100
- Diffusion steps: 50

Submit the epitope-specific binder design job targeting these hotspots.
```

---

## Troubleshooting Prompts

### Check Server Status

```
Check the RFpeptides server status:
1. Get server info to verify installation
2. Show current queue status
3. List any recent jobs
```

**Expected tool calls:**
- `get_server_info()`
- `get_queue_info()`
- `list_jobs()`

### Retry Failed Job

```
My job [JOB_ID] failed. Please:
1. Check the job status and error message
2. Show the job log to understand what went wrong
3. If it's a transient error, resubmit the job
```

**Expected tool calls:**
- `get_job_status(job_id="[JOB_ID]")`
- `get_job_log(job_id="[JOB_ID]", tail=100)`
- `resubmit_job(job_id="[JOB_ID]")`

### Cancel Running Job

```
Cancel my running job [JOB_ID] - I need to change the parameters.
```

**Expected tool calls:**
- `cancel_job(job_id="[JOB_ID]")`

---

## Parameter Guidelines

### Binder Length Recommendations

| Target Type | Recommended Length | Notes |
|-------------|-------------------|-------|
| Concave helical groove | 12-18 residues | MDM2, MCL1 |
| Mixed alpha/beta site | 13-18 residues | GABARAP |
| Flat surface | 14-20 residues | More residues for flat targets |
| Small pocket | 8-12 residues | Smaller binders for tight pockets |

### Number of Designs

| Use Case | Recommended Designs |
|----------|-------------------|
| Quick exploration | 10-25 |
| Standard campaign | 50-100 |
| Comprehensive search | 500-1000 |
| Production run | 5000-10000 |

### Diffusion Steps

| Setting | Steps | Quality vs Speed |
|---------|-------|------------------|
| Fast | 25 | Lower diversity, faster |
| Standard | 50 | Good balance (default) |
| High quality | 100 | Higher diversity, slower |

---

## Next Steps After Backbone Generation

After generating backbones with RFpeptides, the typical workflow continues with:

1. **Sequence Design** (LigandMPNN)
   - Design amino acid sequences for each backbone
   - Generate 8-16 sequences per backbone

2. **Structure Validation** (AfCycDesign)
   - Predict structures from designed sequences
   - Filter by pLDDT > 0.8 and RMSD < 2.0 Å

3. **Binding Analysis**
   - Calculate interface metrics (iPAE, ddG)
   - Filter by iPAE < 0.15

4. **Clustering**
   - Cluster by structural similarity (TMscore)
   - Select diverse representatives

5. **Experimental Validation**
   - Synthesize top candidates
   - Test binding affinity
