# 2025 Paper Processing - Execution Flow Analysis

## Entry Point & Execution Method

Based on repository analysis, here's how the **2025 paper was originally processed**:

---

## **1. ENTRY POINT: `src/main.py`**

The primary entry point is **`src/main.py`** (hardcoded for 2025):

```python
from pathlib import Path
from clean_text import clean_text
from pdf_to_images import pdf_to_images
from ocr import image_to_text

PDF_FILE = "data/pdfs/2025.pdf"  # ← HARDCODED to 2025

images = pdf_to_images(PDF_FILE, "data/images")  # ← HARDCODED output dir
full_text = ""

for image in images:
    print("OCR:", image)
    full_text += image_to_text(image) + "\n\n"

full_text = clean_text(full_text)

Path("data/raw_text").mkdir(parents=True, exist_ok=True)

with open("data/raw_text/ocr_output.txt", "w", encoding="utf-8") as f:  # ← HARDCODED output
    f.write(full_text)

print("Done.")
```

**Original Command:**
```bash
python src/main.py
```

**Outputs:**
- `data/images/page_*.png` - PDF converted to images
- `data/raw_text/ocr_output.txt` - Cleaned OCR text

---

## **2. HARDCODED REFERENCES IN 2025 WORKFLOW**

### **In `src/main.py`:**
```python
PDF_FILE = "data/pdfs/2025.pdf"              # ← Line 7: PDF input (2025)
"data/images"                                 # ← Line 11: Image output directory
"data/raw_text/ocr_output.txt"               # ← Line 31: OCR output filename
```

### **In `src/parser.py`:**
```python
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw_text" / "ocr_output.txt"  # ← Line 17
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "json" / "questions_draft.json"  # ← Line 18
```

**Original Command:**
```bash
python src/parser.py
# (uses defaults, no arguments needed)
```

**Output:**
- `data/json/questions_draft.json` - Structured questions (100 extracted)

### **In `src/analyzer.py`:**
```python
DEFAULT_INPUT = PROJECT_ROOT / "data" / "json" / "questions_draft.json"    # ← Line 18
DEFAULT_TAXONOMY = PROJECT_ROOT / "data" / "taxonomy" / "cgpsc_taxonomy_v1.json"  # ← Line 19
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "analyzed" / "cgpsc_2025_analyzed.json"  # ← Line 20
```

**Original Command:**
```bash
python src/analyzer.py
# (uses defaults, no arguments needed)
```

**Output:**
- `data/analyzed/cgpsc_2025_analyzed.json` - Fully analyzed with taxonomy (year hardcoded as 2025)

---

## **3. YEAR HARDCODING IN PARSER**

**File:** `src/parser.py` line 259:

```python
def build_document(raw_text: str, source: Path) -> dict:
    blocks = segment_questions(raw_text)
    questions = [parse_question(block) for block in blocks]
    # ...
    return {
        "source_file": str(source),
        "exam": "CGPSC Prelims",
        "year": 2025,  # ← LINE 259: HARDCODED YEAR
        "draft": True,
        "summary": { ... },
        "questions": questions,
    }
```

**This means:** Every time parser.py runs, it outputs `year: 2025` regardless of actual data.

---

## **4. COMPLETE 2025 EXECUTION FLOW**

```
Step 1: python src/main.py
   Input:  data/pdfs/2025.pdf
   Output: data/raw_text/ocr_output.txt
   Status: OCR complete (hardcoded paths)
   
Step 2: python src/parser.py
   Input:  data/raw_text/ocr_output.txt
   Output: data/json/questions_draft.json (year=2025, hardcoded)
   Status: 100 questions extracted, 63 flagged for review
   
Step 3: python src/analyzer.py
   Input:  data/json/questions_draft.json
   Taxonomy: data/taxonomy/cgpsc_taxonomy_v1.json
   Output: data/analyzed/cgpsc_2025_analyzed.json (year=2025)
   Status: Fully classified with taxonomy
   
Step 4: python src/validate_analyzer.py
   Input:  data/analyzed/cgpsc_2025_analyzed.json
   Output: Validation report ({"valid": true, "questions": 100})
   
Step 5: python src/statistics.py
   Input:  data/analyzed/cgpsc_2025_analyzed.json (default)
   Output: data/stats/cgpsc_2025_stats.json
   
Step 6: python src/ingest.py data/analyzed/cgpsc_2025_analyzed.json 2025
   Input:  data/analyzed/cgpsc_2025_analyzed.json
   Output: database/questions/2025.json
           database/metadata/2025_metadata.json
           database/stats/cgpsc_2025_stats.json
           database/index.json (updated)
```

---

## **5. EVIDENCE FROM REPOSITORY**

### **Commit History:**
```
1d20a07f: "Reader v1 and Analyzer v1 complete"
          - Initial commit with main.py using "data/pdfs/2025.pdf"
          - parser.py with year=2025 hardcoded

e19adf743b3: "add statistics.py"
             - Generated: data/analyzed/cgpsc_2025_analyzed.json
             - Contains 100 questions with year=2025

```

### **Actual Data Files Present:**

1. **`data/json/questions_draft.json`** (88.7 KB)
   - source_file: `C:\CGPSC-projects\reader\data\raw_text\ocr_output.txt`
   - year: 2025 (line 4)
   - questions_extracted: 100
   - questions_with_four_options: 52
   - flagged_for_review: 63

2. **`data/analyzed/cgpsc_2025_analyzed.json`** (exists)
   - schema_version: "analyzer-record-v1"
   - year: 2025 (line 5)
   - 100 questions with aggregation dict
   - source_file shows Windows path: `C:\CGPSC-projects\reader\data\raw_text\ocr_output.txt`

---

## **6. KEY FINDINGS - HARDCODED PATHS & YEAR REFERENCES**

| File | Line | Hardcoded Value | Type |
|------|------|-----------------|------|
| `src/main.py` | 7 | `"data/pdfs/2025.pdf"` | PDF filename |
| `src/main.py` | 11 | `"data/images"` | Image output dir |
| `src/main.py` | 31 | `"data/raw_text/ocr_output.txt"` | OCR output file |
| `src/parser.py` | 17 | `"data/raw_text/ocr_output.txt"` | Default input |
| `src/parser.py` | 18 | `"data/json/questions_draft.json"` | Default output |
| `src/parser.py` | 259 | `"year": 2025` | Year literal |
| `src/analyzer.py` | 18 | `"data/json/questions_draft.json"` | Default input |
| `src/analyzer.py` | 20 | `"data/analyzed/cgpsc_2025_analyzed.json"` | Default output |

---

## **7. IMPLICATIONS FOR 2024 PROCESSING**

### **Problem:**
- **Year is hardcoded to 2025 in `src/parser.py` line 259**
- Main.py only processes `data/pdfs/2025.pdf`
- All default paths reference 2025 filenames

### **For 2024 to work, you must:**

**Option A (Minimal Changes):**
1. Modify `src/main.py` line 7: `"data/pdfs/2025.pdf"` → `"data/pdfs/2024.pdf"`
2. Modify `src/main.py` lines 11, 31: Use `data/images_2024`, `ocr_output_2024.txt`
3. Modify `src/parser.py` line 259: `"year": 2025` → `"year": 2024`
4. Use command-line args to override defaults in analyzer

**Option B (Current Approach - No Code Changes):**
1. Run parser with explicit year in JSON (requires manual edit after parsing)
2. Use command-line arguments: `python src/analyzer.py input_file -o output_file`
3. Manually pass year to ingest: `python src/ingest.py analyzed_file 2024`

---

## **8. EXECUTION FLOW DIAGRAM**

```
┌─────────────────────────────────┐
│ data/pdfs/2025.pdf (hardcoded)  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ src/main.py                      │
│ - pdf_to_images()               │
│ - image_to_text() [Tesseract]   │
│ - clean_text()                  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ data/raw_text/ocr_output.txt    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ src/parser.py (YEAR=2025)       │
│ - segment_questions()           │
│ - parse_question()              │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ data/json/questions_draft.json  │
│ (100 questions, year=2025)      │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ src/analyzer.py                 │
│ - flatten_taxonomy()            │
│ - classify_taxonomy()           │
│ - classify_difficulty()         │
│ - build_summary()               │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ data/analyzed/                  │
│ cgpsc_2025_analyzed.json        │
│ (100 questions analyzed)        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ src/validate_analyzer.py        │
│ src/statistics.py               │
│ src/ingest.py                   │
│ + database.py                   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ database/                       │
│ ├─ questions/2025.json          │
│ ├─ metadata/2025_metadata.json  │
│ ├─ stats/cgpsc_2025_stats.json  │
│ └─ index.json                   │
└─────────────────────────────────┘
```

---

## **Summary**

**Original 2025 Workflow:**

1. **Entry Point:** `python src/main.py` (hardcoded for 2025.pdf)
2. **OCR Step:** Converts PDF → Images → Text (hardcoded paths)
3. **Parser Step:** `python src/parser.py` (year=2025 hardcoded)
4. **Analyzer Step:** `python src/analyzer.py` (processes draft JSON)
5. **Validation:** `python src/validate_analyzer.py`
6. **Statistics:** `python src/statistics.py`
7. **Ingest:** `python src/ingest.py analyzed.json 2025`

**Key Hardcodings Preventing 2024 Processing:**
- `src/main.py` line 7: PDF filename
- `src/parser.py` line 259: Year literal
- Multiple default paths in `__init__` sections

**To Process 2024:** Either modify year references or use command-line arguments to override defaults.
