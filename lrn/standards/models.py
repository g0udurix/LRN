from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional
import json


@dataclass
class StandardRef:
    body: str
    designation: str
    clause: Optional[str] = None
    title: Optional[str] = None

    def validate(self) -> None:
        if not self.body:
            raise ValueError("StandardRef.body is required")
        if not self.designation:
            raise ValueError("StandardRef.designation is required")


@dataclass
class ClauseMapping:
    jurisdiction: str
    instrument: str
    clause_id: str
    languages: List[str] = field(default_factory=list)
    references: List[StandardRef] = field(default_factory=list)
    notes: Optional[str] = None

    def validate(self) -> None:
        if not self.jurisdiction:
            raise ValueError("ClauseMapping.jurisdiction is required")
        if not self.instrument:
            raise ValueError("ClauseMapping.instrument is required")
        if not self.clause_id:
            raise ValueError("ClauseMapping.clause_id is required")
        if not self.languages:
            raise ValueError("ClauseMapping.languages must include at least one language")
        for ref in self.references:
            ref.validate()


def _mapping_from_dict(raw: dict) -> ClauseMapping:
    references = [StandardRef(**ref) for ref in raw.get('references', [])]
    mapping = ClauseMapping(
        jurisdiction=raw.get('jurisdiction', ''),
        instrument=raw.get('instrument', ''),
        clause_id=raw.get('clause_id', ''),
        languages=list(raw.get('languages', [])),
        references=references,
        notes=raw.get('notes'),
    )
    mapping.validate()
    return mapping


def load_mappings(path: Path) -> List[ClauseMapping]:
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, list):
        raise ValueError("mapping file must contain a list")
    return [_mapping_from_dict(item) for item in data]


def validate_mapping_file(path: Path) -> None:
    load_mappings(path)


def to_dict(mapping: ClauseMapping) -> dict:
    return {
        'jurisdiction': mapping.jurisdiction,
        'instrument': mapping.instrument,
        'clause_id': mapping.clause_id,
        'languages': mapping.languages,
        'references': [ref.__dict__ for ref in mapping.references],
        'notes': mapping.notes,
    }


def dump_mappings(mappings: Iterable[ClauseMapping], path: Path) -> None:
    serialized = [to_dict(m) for m in mappings]
    path.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding='utf-8')
