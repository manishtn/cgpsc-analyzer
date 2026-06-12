# CGPSC Analyzer v1

Analyzer v1 enriches Reader output with taxonomy-driven subject, topic,
subtopic, and difficulty classifications.

## Run

From the project root:

```powershell
python src/analyzer.py
python src/validate_analyzer.py
```

Output:

```text
data/analyzed/cgpsc_2025_analyzed.json
```

## Classification Model

The classifier engine is generic. Classification knowledge lives in:

```text
data/taxonomy/cgpsc_taxonomy_v1.json
```

Each question receives:

- Stable `record_id`
- Versioned taxonomy path
- Primary subject, topic, and subtopic IDs
- Confidence, matched evidence, alternatives, and review status
- Difficulty label, score, and evidence
- Flat aggregation keys for multi-year analysis

Options are treated as secondary evidence because ~Reader OCR may place option
text incorrectly. To improve classifications, edit taxonomy terms and weights
instead of adding question-specific Python conditions.

## Difficulty

Difficulty is currently a configurable structural estimate based on question
type and reasoning signals. It is not an empirical measure. Later, response
accuracy and time-to-answer data can replace or supplement this estimate while
preserving the same output schema.

## Multi-Year Usage

Run Analyzer separately for each year's Reader JSON. Records can later be
combined using:

- `record_id`
- `year`
- `aggregation.subject_id`
- `aggregation.topic_id`
- `aggregation.subtopic_id`
- `aggregation.question_type`
- `aggregation.difficulty`

Do not rename taxonomy IDs after publishing analyzed records. Add new taxonomy
versions or aliases when categories change.
