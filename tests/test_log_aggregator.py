import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_AGGREGATOR = REPO_ROOT / "tools" / "log_aggregator.py"


def run_log_aggregator(*args):
    return subprocess.run(
        [sys.executable, str(LOG_AGGREGATOR), *map(str, args)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_no_input_exits_with_usage_error():
    result = run_log_aggregator()

    assert result.returncode != 0
    assert "usage:" in result.stderr.lower()
    assert "--input" in result.stderr
    assert "--dir" in result.stderr
    assert "traceback" not in result.stderr.lower()


def test_empty_file_exports_zero_entry_report(tmp_path):
    empty_log = tmp_path / "empty.log"
    output = tmp_path / "report.json"
    empty_log.write_text("", encoding="utf-8")

    result = run_log_aggregator("--input", empty_log, "--output", output)

    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["summary"]["total_entries"] == 0
    assert report["summary"]["time_range"] is None
    assert "Total entries: 0" in result.stdout
    assert "Time range: N/A to N/A" in result.stdout
    assert "traceback" not in result.stderr.lower()


def test_missing_input_file_is_reported_without_traceback(tmp_path):
    missing_log = tmp_path / "missing.log"
    output = tmp_path / "report.json"

    result = run_log_aggregator("--input", missing_log, "--output", output)

    assert result.returncode != 0
    assert str(missing_log) in result.stderr
    assert "not found" in result.stderr.lower()
    assert not output.exists()
    assert "traceback" not in result.stderr.lower()


def test_successful_json_export_includes_parsed_entries(tmp_path):
    app_log = tmp_path / "app.log"
    output = tmp_path / "report.json"
    app_log.write_text(
        "2024-01-15 12:00:00 [api] INFO request complete\n",
        encoding="utf-8",
    )

    result = run_log_aggregator("--input", app_log, "--output", output)

    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["summary"]["total_entries"] == 1
    assert report["summary"]["by_level"] == {"info": 1}
    assert report["summary"]["by_service"] == {"api": 1}
    assert report["entries"][0]["message"].endswith("request complete")
