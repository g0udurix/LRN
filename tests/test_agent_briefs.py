from __future__ import annotations

from pathlib import Path

import pytest

AGENT_DIR = Path('docs/agents')
AGENT_FILES = [
    'strategist.md',
    'governance_runner.md',
    'corpus_wrangler.md',
    'standards_mapper.md',
    'persistence_architect.md',
]

REQUIRED_HEADINGS = [
    '# ',  # top-level title
    '## Core Responsibilities',
    '## Workflow',
    '## Exit Checklist',
]

@pytest.mark.parametrize('agent_file', AGENT_FILES)
def test_agent_brief_exists(agent_file: str) -> None:
    path = AGENT_DIR / agent_file
    assert path.exists(), f"Missing agent brief: {path}"


@pytest.mark.parametrize('agent_file', AGENT_FILES)
def test_agent_brief_has_required_sections(agent_file: str) -> None:
    content = (AGENT_DIR / agent_file).read_text(encoding='utf-8')
    for heading in REQUIRED_HEADINGS:
        assert heading in content, f"{agent_file} missing heading '{heading}'"


@pytest.mark.parametrize('agent_file', AGENT_FILES)
def test_agent_brief_mentions_pytest(agent_file: str) -> None:
    content = (AGENT_DIR / agent_file).read_text(encoding='utf-8').lower()
    assert ('python -m pytest' in content or 'python - m pytest' in content), (
        f"{agent_file} should reference running pytest to keep hand-offs consistent"
    )


@pytest.mark.parametrize('agent_file', AGENT_FILES)
def test_agent_brief_mentions_logging(agent_file: str) -> None:
    content = (AGENT_DIR / agent_file).read_text(encoding='utf-8').lower()
    assert 'log' in content, f"{agent_file} should mention logging expectations"
