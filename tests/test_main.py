import sys
from pathlib import Path
import pytest
from main import main, process_pipeline


def test_process_pipeline_files_only(tmp_path: Path):
    file_path = Path("data/input/sample_valid_1.pdf")
    report = process_pipeline(input_files=[file_path], output_dir=tmp_path)

    assert len(report.valid_records) > 0
    assert (tmp_path / "records.csv").exists()
    assert (tmp_path / "records.json").exists()
    assert (tmp_path / "validation_report.json").exists()
    assert (tmp_path / "tax_report.pdf").exists()


def test_process_pipeline_dir(tmp_path: Path):
    report = process_pipeline(input_dir=Path("data/input"), output_dir=tmp_path)

    assert len(report.valid_records) > 0
    assert (tmp_path / "records.csv").exists()
    assert (tmp_path / "records.json").exists()


def test_process_pipeline_missing_dir(tmp_path: Path):
    missing_dir = tmp_path / "nonexistent"
    report = process_pipeline(input_dir=missing_dir, output_dir=tmp_path)

    assert len(report.valid_records) == 0
    assert len(report.errors) == 0


def test_process_pipeline_unsupported_and_missing_files(tmp_path: Path):
    valid_file = Path("data/input/sample_valid_1.pdf")
    missing_file = tmp_path / "missing.pdf"
    unsupported_file = tmp_path / "notes.txt"
    unsupported_file.write_text("tax notes")

    report = process_pipeline(
        input_files=[valid_file, missing_file, unsupported_file],
        output_dir=tmp_path,
    )

    assert len(report.valid_records) > 0


def test_cli_dir_default(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        sys, "argv", ["main.py", "--dir", "--output-dir", str(tmp_path)]
    )
    main()
    assert (tmp_path / "records.csv").exists()


def test_cli_dir_custom(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "--dir", "data/input", "--output-dir", str(tmp_path)],
    )
    main()
    assert (tmp_path / "records.csv").exists()


def test_cli_files_mode(monkeypatch, tmp_path: Path):
    file_path = "data/input/sample_valid_1.pdf"
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", file_path, "--output-dir", str(tmp_path)],
    )
    main()
    assert (tmp_path / "records.csv").exists()


def test_cli_no_args_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["main.py"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code != 0
    captured = capsys.readouterr()
    assert "No input files provided" in captured.err


def test_cli_conflicting_args_error(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "data/input/sample_valid_1.pdf", "--dir", "data/input"],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code != 0
    captured = capsys.readouterr()
    assert "Cannot specify both file inputs and the '--dir' flag" in captured.err


def test_cli_dir_as_file_arg_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["main.py", "data/input"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code != 0
    captured = capsys.readouterr()
    assert "is a directory. Use '--dir" in captured.err


def test_cli_summary_output(monkeypatch, capfd, tmp_path: Path):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "data/input/sample_valid_1.pdf", "--output-dir", str(tmp_path)],
    )
    main()
    captured = capfd.readouterr()
    assert "BAYTAXPRO PROCESSING SUMMARY" in captured.out
    assert "Total files scanned:" in captured.out
    assert "Valid records exported:" in captured.out
    assert "CSV Export:" in captured.out

