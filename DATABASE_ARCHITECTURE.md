# CGPSC Intelligence System - Multi-Year Database Architecture

## Overview

The database system enables storage, retrieval, and aggregation of CGPSC exam papers across multiple years (2025, 2024, 2023, etc.) for trend analysis.

---

## Directory Structure

```
database/
├── questions/           # Analyzed papers by year
│   ├── 2025.json       # 100 questions from 2025 exam
│   ├── 2024.json       # 100 questions from 2024 exam
│   ├── 2023.json       # 100 questions from 2023 exam
│   └── ...
├── metadata/           # Paper metadata (ingestion tracking)
│   ├── 2025_metadata.json
│   ├── 2024_metadata.json
│   └── ...
├── stats/              # Generated statistics by year
│   ├── cgpsc_2025_stats.json
│   ├── cgpsc_2024_stats.json
│   └── ...
└── index.json          # Quick lookup index
```

---

## Core Components

### 1. **database.py** - PaperDatabase Class

```python
from src.database import PaperDatabase

# Initialize
db = PaperDatabase()

# Ingest a paper
success, msg = db.ingest_paper(
    analyzed_file=Path("data/analyzed/cgpsc_2025_analyzed.json"),
    year=2025,
    overwrite=False
)

# Load paper
paper_2025 = db.load_paper(2025)
questions_2025 = db.load_questions(2025)
metadata_2025 = db.load_metadata(2025)

# List all papers
years = db.list_papers()  # [2025, 2024, 2023]

# Get all metadata
all_papers = db.get_papers_metadata()

# Show status
db.print_database_status()
```

**Key Methods:**
- `ingest_paper()` - Store analyzed JSON with validation
- `load_paper()` - Retrieve full paper
- `load_questions()` - Get question list
- `load_metadata()` - Get paper metadata
- `list_papers()` - Get all available years
- `paper_exists()` - Check if year exists
- `get_index()` - Query database index

---

### 2. **ingest.py** - Paper Ingestion Workflow

```bash
# Ingest 2025 paper
python src/ingest.py data/analyzed/cgpsc_2025_analyzed.json 2025

# Ingest 2024 paper (with overwrite)
python src/ingest.py data/analyzed/cgpsc_2024_analyzed.json 2024 --overwrite

# Skip statistics generation
python src/ingest.py data/analyzed/cgpsc_2024_analyzed.json 2024 --skip-stats

# Verbose output
python src/ingest.py data/analyzed/cgpsc_2025_analyzed.json 2025 -v
```

**Workflow Steps:**
1. ✓ Validate analyzer output format
2. ✓ Ingest into database/questions/{year}.json
3. ✓ Store metadata with ingestion timestamp
4. ✓ Generate statistics (automatic)
5. ✓ Update database index
6. ✓ Print status report

---

## Usage Pattern: Processing a New Year

### Step 1: Run Analyzer (existing pipeline)
```bash
python src/analyzer.py data/json/questions_draft_2024.json \
  -t data/taxonomy/cgpsc_taxonomy_v1.json \
  -o data/analyzed/cgpsc_2024_analyzed.json
```

Output: `data/analyzed/cgpsc_2024_analyzed.json` ✓

### Step 2: Ingest into Database
```bash
python src/ingest.py data/analyzed/cgpsc_2024_analyzed.json 2024
```

Output:
```
Step 1: Validating input file...
  Valid analyzer record for 2024 (100 questions)

Step 2: Ingesting paper into database...
  ✓ Paper for 2024 ingested successfully (100 questions)

Step 3: Generating statistics...
  Statistics generated: database/stats/cgpsc_2024_stats.json

Step 4: Database status...
  CGPSC INTELLIGENCE DATABASE STATUS
  Total Papers: 2
  
  Year     Exam                 Questions    Ingested
  2025     CGPSC Prelims        100          2026-06-12
  2024     CGPSC Prelims        100          2026-06-12
  
  Total Questions Across All Papers: 200
```

### Step 3: Database Contains Both Years
- ✓ `database/questions/2025.json` (100 questions)
- ✓ `database/questions/2024.json` (100 questions)
- ✓ `database/stats/cgpsc_2025_stats.json`
- ✓ `database/stats/cgpsc_2024_stats.json`
- ✓ `database/index.json` (lookup index)

---

## Data Flow

```
Analyzer Output                Database Storage              Statistics
─────────────────              ────────────────              ──────────
2024_analyzed.json     →    questions/2024.json     →    stats/cgpsc_2024_stats.json
  100 questions                Validated & stored         Subjects, topics, etc.
  aggregation dict                                        Count validation
  
2025_analyzed.json     →    questions/2025.json     →    stats/cgpsc_2025_stats.json
  100 questions                Validated & stored         Subjects, topics, etc.
  aggregation dict                                        Count validation

                          metadata/
                          ├─ 2024_metadata.json
                          ├─ 2025_metadata.json
                          
                          index.json (quick lookup)
```

---

## Schema: Paper Storage Format

Each year's paper is stored as the full analyzer output:

```json
{
  "schema_version": "analyzer-record-v1",
  "taxonomy_version": "cgpsc-taxonomy-v1.0.0",
  "exam": "CGPSC Prelims",
  "year": 2025,
  "source_file": "...",
  "summary": {
    "questions": 100,
    "subjects": { "history": 11, ... },
    "topics": { "history.ancient": 8, ... },
    "difficulty": { "easy": 76, "medium": 16, "hard": 8 }
  },
  "questions": [
    {
      "question_no": 1,
      "record_id": "cgpsc-prelims-2025-q001",
      "aggregation": {
        "subject_id": "history",
        "topic_id": "history.ancient",
        "subtopic_id": "history.ancient.kingdoms",
        "difficulty": "easy",
        "question_type": "standard_mcq"
      }
      // ... full question data
    },
    // ... 99 more questions
  ]
}
```

---

## Metadata Format

```json
{
  "year": 2025,
  "exam": "CGPSC Prelims",
  "total_questions": 100,
  "taxonomy_version": "cgpsc-taxonomy-v1.0.0",
  "ingested_at": "2026-06-12T10:30:00.000000",
  "source_file": "data/analyzed/cgpsc_2025_analyzed.json",
  "schema_version": "analyzer-record-v1"
}
```

---

## Index Format

```json
{
  "2025": {
    "year": 2025,
    "exam": "CGPSC Prelims",
    "total_questions": 100,
    "taxonomy_version": "cgpsc-taxonomy-v1.0.0",
    "ingested_at": "2026-06-12T10:30:00.000000"
  },
  "2024": {
    "year": 2024,
    "exam": "CGPSC Prelims",
    "total_questions": 100,
    "taxonomy_version": "cgpsc-taxonomy-v1.0.0",
    "ingested_at": "2026-06-12T10:35:00.000000"
  }
}
```

---

## Future: Multi-Year Trend Analysis

Once multiple years are ingested, the trend analysis pipeline will:

```python
from src.database import PaperDatabase
from src.statistics import StatisticsGenerator

db = PaperDatabase()

# Get all papers
years = db.list_papers()  # [2025, 2024, 2023, 2022, 2021]

# Load statistics for each year
stats = {}
for year in years:
    stats_path = db.db_root / "stats" / f"cgpsc_{year}_stats.json"
    with open(stats_path) as f:
        stats[year] = json.load(f)

# Aggregate across years
# → Identify trends in subject distribution
# → Track difficulty changes over time
# → Analyze question type evolution
# → Detect taxonomy migration patterns
```

---

## Validation & Error Handling

### Input Validation
- ✓ File exists
- ✓ Valid JSON
- ✓ Schema version = "analyzer-record-v1"
- ✓ Year matches metadata
- ✓ Has questions array

### Ingest Validation
- ✓ Year consistency check
- ✓ Duplicate prevention (with overwrite option)
- ✓ Metadata integrity
- ✓ Statistics count validation (100 questions)

### Database Operations
- ✓ Graceful error messages
- ✓ Detailed logging at INFO level
- ✓ Transaction-like integrity (save metadata + index together)

---

## Next Steps

### Immediate (Ready Now)
1. ✓ Process 2024 using existing analyzer pipeline
2. ✓ Ingest 2024 into database
3. ✓ Verify database contains both 2025 and 2024

### Near-Term (Planned)
1. Process 2023, 2022, 2021, 2020, 2019
2. Ingest each year into database
3. Validate total: 7 years × 100 questions = 700+ questions

### Trend Analysis (Future)
1. Identify subject popularity trends
2. Track topic distribution changes
3. Analyze difficulty evolution
4. Detect taxonomy updates
5. Generate trend reports and visualizations

---

## Quick Reference

| Task | Command |
|------|---------|
| Ingest 2025 | `python src/ingest.py data/analyzed/cgpsc_2025_analyzed.json 2025` |
| Ingest 2024 | `python src/ingest.py data/analyzed/cgpsc_2024_analyzed.json 2024` |
| List all years | `python -c "from src.database import PaperDatabase; print(PaperDatabase().list_papers())"` |
| Show status | `python -c "from src.database import PaperDatabase; PaperDatabase().print_database_status()"` |
| Load 2025 questions | `python -c "from src.database import PaperDatabase; print(len(PaperDatabase().load_questions(2025)))"` |

---

## Module Dependencies

```
ingest.py (Workflow Orchestrator)
  ├── database.py (PaperDatabase)
  ├── statistics.py (StatisticsGenerator)
  └── analyzer.py (validation reference)

database.py (Paper Storage)
  └── (no dependencies - standalone)

statistics.py (Statistics Generation)
  └── (no dependencies - standalone)
```

All modules can be used independently or together in the workflow.
