# Standards Mapping Overview

Phase 1 introduces a lightweight schema for linking LegisQuébec clauses to external standards (CSA/ANSI/ISO).

## Data Model
- `StandardRef`: identifies an external document (body, designation, clause, optional title).
- `ClauseMapping`: associates a LegisQuébec clause with one or more `StandardRef` entries and optional notes.

Mappings are stored as JSON/YAML arrays and validated via `lrn.standards.validate_mapping_file()`.

## Example
```json
[
  {
    "jurisdiction": "QC",
    "instrument": "S-2.1",
    "clause_id": "section-51",
    "languages": ["fr", "en"],
    "references": [
      {"body": "CSA", "designation": "Z462-21", "clause": "4.1"}
    ],
    "notes": "Align PPE requirements"
  }
]
```

Run validation:
```bash
python -m lrn.standards validate docs/standards/examples/sample.json
```
