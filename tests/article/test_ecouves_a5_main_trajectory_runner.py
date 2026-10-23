"""Lightweight tests for the Q-9F.2 command-line runner infrastructure."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts" / "article" / "run_ecouves_a5_main_trajectory.py"


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_ecouves_a5_main_trajectory", RUNNER_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sha256_matches_hashlib(tmp_path):
    runner = load_runner()
    source = tmp_path / "initial_state.npz"
    content = b"Q-9F.2 reproducibility fixture\n"
    source.write_bytes(content)

    assert runner.sha256(source) == hashlib.sha256(content).hexdigest()


def test_refuse_nonempty_output_creates_missing_directory(tmp_path):
    runner = load_runner()
    output_dir = tmp_path / "new_output"

    runner.refuse_nonempty_output(output_dir, overwrite=False)

    assert output_dir.is_dir()
    assert list(output_dir.iterdir()) == []


def test_refuse_nonempty_output_accepts_empty_directory(tmp_path):
    runner = load_runner()
    output_dir = tmp_path / "empty_output"
    output_dir.mkdir()

    runner.refuse_nonempty_output(output_dir, overwrite=False)

    assert output_dir.is_dir()
    assert list(output_dir.iterdir()) == []


def test_refuse_nonempty_output_rejects_existing_results(tmp_path):
    runner = load_runner()
    output_dir = tmp_path / "existing_output"
    output_dir.mkdir()
    (output_dir / "result.csv").write_text("value\n1\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="Refusing to overwrite non-empty Q-9F.2"):
        runner.refuse_nonempty_output(output_dir, overwrite=False)


def test_refuse_nonempty_output_allows_explicit_overwrite(tmp_path):
    runner = load_runner()
    output_dir = tmp_path / "existing_output"
    output_dir.mkdir()
    existing = output_dir / "result.csv"
    existing.write_text("value\n1\n", encoding="utf-8")

    runner.refuse_nonempty_output(output_dir, overwrite=True)

    assert existing.exists()
