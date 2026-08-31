# 🤖 Agentic RFP Evaluation System

An AI-assisted RFP evaluation and supplier ranking system built using Python, Streamlit, SQLite, Pydantic, PyMuPDF, and OpenRouter.

The application evaluates multiple supplier RFP proposals against configurable evaluation criteria and produces a deterministic supplier ranking.

## Project Overview

The system evaluates supplier proposals using:

- PDF document extraction
- LLM-based proposal evaluation
- Pydantic validation
- Deterministic weighted scoring
- Peer benchmarking
- Criterion-level gap analysis
- Relative performance calculation
- Peer Performance Index (PPI)
- Deterministic supplier ranking
- SQLite persistence
- Streamlit presentation

The LLM is responsible only for evaluating proposal content. Scoring, benchmarking, PPI, and ranking are performed using deterministic Python logic.

## Architecture

```text
Supplier RFP PDFs
       |
       v
PDF Document Tool
       |
       v
Evaluation Agent
(OpenRouter / Qwen)
       |
       v
Validation Tool
(Pydantic)
       |
       v
Ranking Tool
(Deterministic Python)
       |
       +--> Weighted Score
       +--> Peer Benchmark
       +--> Criterion Gap
       +--> Relative Performance
       +--> PPI
       +--> Tie-break Ranking
       |
       v
SQLite Persistence
       |
       v
Streamlit Presentation
```

## Project Structure

```text
raj_ai_mini_project/
├── app.py
├── database.py
├── pdf_utils.py
├── evaluation.py
├── validation.py
├── ranking.py
├── seed_db.py
├── requirements.txt
├── README.md
├── data/
│   └── rfp_evaluation.db
├── sample_rfps/
│   ├── Apex_Systems.pdf
│   ├── BrightPath_Tech.pdf
│   ├── NexaWorks.pdf
│   └── Orbit_Digital.pdf
└── sample_output/
    └── sample_result.json
```

## Evaluation Criteria

| Criterion | Weight | Maximum Score |
|---|---:|---:|
| Technical Capability | 30% | 10 |
| Implementation Plan | 20% | 10 |
| Commercial Value | 20% | 10 |
| Security & Compliance | 20% | 10 |
| Support & Experience | 10% | 10 |
| **Total** | **100%** | |

Criteria are stored in SQLite and loaded dynamically.

## Scoring

For each criterion:

```text
Weighted Contribution =
(score / maximum score) × criterion weight
```

Example:

```text
Score = 8
Maximum Score = 10
Weight = 30%

Contribution = (8 / 10) × 30 = 24
```

## Peer Benchmark

For each criterion:

```text
Benchmark = Highest supplier score
```

## Criterion Gap

```text
Gap = Supplier Score - Peer Benchmark
```

## Relative Performance

```text
Relative Performance =
Supplier Score / Peer Benchmark × 100
```

The zero-benchmark case is handled safely to avoid division by zero.

## Peer Performance Index (PPI)

PPI is the weighted average of the supplier's relative performance across all active criteria.

## Deterministic Ranking

Tie-break order:

1. Higher PPI
2. Earlier submission date
3. Higher historical experience rating
4. Supplier name ascending

The LLM is not used for ranking.

## Validation

The validation layer uses Pydantic and checks:

- JSON validity
- Required schema
- Criterion presence
- Score range
- Maximum score
- Unexpected criteria
- Missing criteria

Recoverable issues are normalized and reported as warnings.

## SQLite Database

The database contains:

### `evaluation_criteria`

Stores criterion ID, name, description, weight, maximum score, and active status.

### `rfp_runs`

Stores RFP Run ID, creation timestamp, and run status.

### `supplier_results`

Stores supplier metadata, absolute score, PPI, final rank, and complete JSON result.

All suppliers evaluated in one batch share the same `rfp_run_id`.

## Database Setup

Recreate the database with:

```bash
python seed_db.py
```

The script creates the required tables and inserts the five active evaluation criteria. Active weights are validated to total 100%.

## Installation

```bash
git clone https://github.com/rajkumartho/raj_ai_mini_project.git
cd raj_ai_mini_project
pip install -r requirements.txt
```

## OpenRouter API Key

The application requires an OpenRouter API key.

Do **not** put the API key directly in source code or commit it to GitHub.

For local execution, configure the `OPENROUTER_API_KEY` environment variable.

Windows PowerShell:

```powershell
$env:OPENROUTER_API_KEY="your-api-key"
```

For Streamlit Community Cloud, configure the key using Streamlit Secrets.

## Run the Application

```bash
streamlit run app.py
```

The application provides:

- 📋 Criteria
- 📄 Supplier Evaluation
- 🏆 Leaderboard
- 🔎 Run Details

## Evaluation Workflow

```text
Upload Supplier PDFs
        |
        v
Create RFP_RUN_ID
        |
        v
Extract PDF Text
        |
        v
Load Active Criteria
        |
        v
OpenRouter / Qwen
        |
        v
Validate LLM JSON
        |
        v
Calculate Weighted Scores
        |
        v
Calculate Peer Benchmarks
        |
        v
Calculate Criterion Gaps
        |
        v
Calculate Relative Performance
        |
        v
Calculate PPI
        |
        v
Apply Deterministic Ranking
        |
        v
Save Results to SQLite
        |
        v
Display Leaderboard
```

## Sample Supplier RFPs

The repository includes four synthetic supplier proposals:

- Apex Systems
- BrightPath Tech
- NexaWorks
- Orbit Digital

## Sample Output

A sample JSON result is provided in:

```text
sample_output/sample_result.json
```

It contains supplier information, scores, PPI, rank, criterion details, benchmarks, gaps, relative performance, evidence, risks, warnings, and overall summary.

## Streamlit Community Cloud Deployment

Repository:

```text
rajkumartho/raj_ai_mini_project
```

Main application file:

```text
app.py
```

Configure the OpenRouter API key in Streamlit Secrets:

```toml
OPENROUTER_API_KEY = "your-api-key"
```

Never commit the API key to GitHub.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Web application |
| OpenRouter | LLM API |
| Qwen | Proposal evaluation |
| PyMuPDF | PDF text extraction |
| Pydantic | Output validation |
| SQLite | Persistence |
| Pandas | Data handling |

## Security

- API keys are not stored in source code.
- API keys are supplied through environment variables or Streamlit Secrets.
- Supplier documents are synthetic project data.
- LLM output is validated before deterministic calculations.
- Ranking is not delegated to the LLM.

## Project Objective

This project demonstrates an agentic RFP evaluation workflow where supplier documents are processed automatically, an AI evaluation agent evaluates proposal content, validation protects downstream calculations, deterministic Python logic calculates scores and ranking, peer comparison provides relative performance, SQLite provides persistence, and Streamlit provides an interactive user interface.

## Author

**Rajkumar Thota**

GitHub: https://github.com/rajkumartho/raj_ai_mini_project

## Project Type

Mini Project — Agentic RFP Evaluation and Supplier Ranking System
