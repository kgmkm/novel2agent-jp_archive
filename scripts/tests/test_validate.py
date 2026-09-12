"""scripts/tests/test_validate.py — validate.py の受け入れテスト

fixtures:
  ok/          エラー0・警告0
  bad_id/      ファイル名=ID 不一致
  bad_version/ versions 章範囲重複
  bad_syntax/  構文エラー（検証続行）
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
SCRIPT = HERE.parent / "validate.py"
FIXTURES = HERE / "fixtures"
WORK = HERE / ".work"
PY = sys.executable


def run(project: Path, *extra):
    proc = subprocess.run(
        [PY, str(SCRIPT), "--project-dir", str(project), *extra],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout + proc.stderr)


@pytest.fixture()
def ok_project():
    dst = WORK / "ok"
    shutil.copytree(FIXTURES / "ok", dst, dirs_exist_ok=True)
    yield dst
    shutil.rmtree(dst, ignore_errors=True)


def copy_case(name: str) -> Path:
    dst = WORK / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(FIXTURES / name, dst)
    return dst


@pytest.mark.parametrize("case", ["bad_id", "bad_version", "bad_syntax"])
def test_negative_cases_exit_1(case: str):
    p = copy_case(case)
    code, out = run(p)
    assert code == 1, out


def test_id_mismatch_detected():
    code, out = run(copy_case("bad_id"))
    assert "ファイル名=ID 不一致" in out


def test_version_overlap_detected():
    code, out = run(copy_case("bad_version"))
    assert "章範囲重複" in out


def test_syntax_error_reports_but_continues():
    code, out = run(copy_case("bad_syntax"))
    assert "構文エラー" in out
    assert "検証結果" in out  # 他ファイルの検証結果は出力されている


def test_proposed_leaves_warning_but_exits_0():
    p = copy_case("ok_proposed")
    code, out = run(p)
    assert code == 0, out
    assert "proposed 残留" in out          # established
    assert "summary_status = proposed" in out


def test_ok_project_passes(ok_project):
    code, out = run(ok_project)
    assert code == 0, out
    assert "[ERROR]" not in out
    assert "エラー 0 件 / 警告 0 件" in out


def test_index_outputs_ids(ok_project):
    code, out = run(ok_project, "--index")
    assert code == 0, out
    assert "chara-001" in out and "桜井美咲" in out
    assert "world-001" in out
    assert "plot-ch01" in out and "覚醒" in out
