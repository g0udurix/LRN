from pathlib import Path

import pytest

from lrn.standards import ClauseMapping, StandardRef, load_mappings, validate_mapping_file


def test_standard_ref_validation():
    ref = StandardRef(body="CSA", designation="Z462-21")
    ref.validate()

    with pytest.raises(ValueError):
        StandardRef(body="", designation="Z462-21").validate()

    with pytest.raises(ValueError):
        StandardRef(body="CSA", designation="").validate()


def test_clause_mapping_validation():
    mapping = ClauseMapping(
        jurisdiction="QC",
        instrument="S-2.1",
        clause_id="section-51",
        languages=["fr", "en"],
        references=[StandardRef(body="CSA", designation="Z462-21")],
    )
    mapping.validate()

    with pytest.raises(ValueError):
        ClauseMapping(jurisdiction="", instrument="S-2.1", clause_id="x", languages=["fr"]).validate()


def test_load_mappings(tmp_path: Path):
    path = tmp_path / "mapping.json"
    path.write_text(
        """
        [
          {
            "jurisdiction": "QC",
            "instrument": "S-2.1",
            "clause_id": "section-51",
            "languages": ["fr", "en"],
            "references": [{"body": "CSA", "designation": "Z462-21"}]
          }
        ]
        """,
        encoding="utf-8",
    )
    mappings = load_mappings(path)
    assert mappings[0].references[0].body == "CSA"

    with pytest.raises(ValueError):
        bad = tmp_path / "bad.json"
        bad.write_text("{}", encoding="utf-8")
        load_mappings(bad)


def test_validate_mapping_file_against_example():
    root = Path(__file__).resolve().parents[1]
    validate_mapping_file(root / "docs/standards/examples/sample.json")
