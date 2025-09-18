from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import runner


def _prepare_templates(tmp_path: Path) -> tuple[Path, Path]:
    template_dir = tmp_path / "templates"
    repo_root = tmp_path / "repo"
    template_dir.mkdir()
    repo_root.mkdir()

    (template_dir / "file.txt").write_text("hello", encoding="utf-8")
    (template_dir / "nested").mkdir()
    (template_dir / "nested" / "config.yml").write_text("key: value\n", encoding="utf-8")

    # Ensure repo has an outdated file for testing
    (repo_root / "file.txt").write_text("old", encoding="utf-8")
    (repo_root / "nested").mkdir()
    (repo_root / "nested" / "config.yml").write_text("old-config", encoding="utf-8")
    return template_dir, repo_root


def test_discover_templates(tmp_path: Path) -> None:
    template_dir, repo_root = _prepare_templates(tmp_path)
    entries = runner.discover_templates(template_dir, repo_root)
    relative_paths = {entry.destination.relative_to(repo_root) for entry in entries}
    assert relative_paths == {Path("file.txt"), Path("nested/config.yml")}


def test_find_mismatches_detects_missing_and_diff(tmp_path: Path) -> None:
    template_dir, repo_root = _prepare_templates(tmp_path)
    entries = runner.discover_templates(template_dir, repo_root)

    # Remove one destination to simulate missing file
    (repo_root / "nested" / "config.yml").unlink()

    mismatches = runner.find_mismatches(entries)
    assert {entry.destination.relative_to(repo_root) for entry in mismatches} == {
        Path("file.txt"),
        Path("nested/config.yml"),
    }


def test_apply_templates_writes_files(tmp_path: Path) -> None:
    template_dir, repo_root = _prepare_templates(tmp_path)
    entries = runner.discover_templates(template_dir, repo_root)

    runner.apply_templates(entries)

    assert (repo_root / "file.txt").read_text(encoding="utf-8") == "hello"
    assert (repo_root / "nested" / "config.yml").read_text(encoding="utf-8") == "key: value\n"


def test_cli_self_test_reports_mismatch(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    template_dir, repo_root = _prepare_templates(tmp_path)
    entries = runner.discover_templates(template_dir, repo_root)
    # Simulate missing file
    (repo_root / "nested" / "config.yml").unlink()
    exit_code = runner.main([
        "--self-test",
        "--template-dir",
        str(template_dir),
        "--repo-root",
        str(repo_root),
    ])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "nested/config.yml" in captured.out


def test_cli_apply_dry_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    template_dir, repo_root = _prepare_templates(tmp_path)
    exit_code = runner.main([
        "--apply",
        "--dry-run",
        "--template-dir",
        str(template_dir),
        "--repo-root",
        str(repo_root),
    ])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "DRY-RUN" in captured.out
    # Ensure file not overwritten
    assert (repo_root / "file.txt").read_text(encoding="utf-8") == "old"


def test_cli_apply_executes_copy(tmp_path: Path) -> None:
    template_dir, repo_root = _prepare_templates(tmp_path)
    runner.main([
        "--apply",
        "--template-dir",
        str(template_dir),
        "--repo-root",
        str(repo_root),
    ])
    assert (repo_root / "file.txt").read_text(encoding="utf-8") == "hello"
    assert (repo_root / "nested" / "config.yml").exists()
