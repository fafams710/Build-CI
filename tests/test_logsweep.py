import pytest
import sys

from logsweep import main, sweep

def test_sweep_empty(tmp_path, capsys):
    errors = sweep(str(tmp_path))
    captured = capsys.readouterr()

    assert errors == 0
    assert "no log files here" in captured.out

def test_sweep_non_log_file(tmp_path, capsys):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "INFO line 1\nWARN line 1\nERROR line 1\nERROR line 2\n"
    )
    (tmp_path / "not_a_log.txt").write_text("this is not a log file")

    errors = sweep(str(tmp_path))
    captured = capsys.readouterr()
    

    (tmp_path / "not_a_log.txt").write_text("this is not a log file")

    assert errors == 2
    assert "app.log            1 info   1 warn   2 error" in captured.out
    assert "worst file: app.log" in captured.out
    assert "not_a_log.txt" not in captured.out

def test_sweep_worst_file_identifier(tmp_path, capsys):

    (tmp_path / "depot-mon.log").write_text(
        "INFO  depot opened\n"
        "INFO  van 1 loaded\n"
        "WARN  van 2 late\n"
        "INFO  van 2 loaded\n"
        "ERROR crate 88 damaged\n"
        "INFO  depot closed\n"
    )


    (tmp_path / "depot-tue.log").write_text(
        "INFO  depot opened\n"
        "INFO  van 1 loaded\n"
        "INFO  van 2 loaded\n"
        "INFO  depot closed\n"
    )


    (tmp_path / "depot-wed.log").write_text(
        "INFO  depot opened\n"
        "ERROR scanner offline\n"
        "ERROR scanner offline\n"
        "WARN  falling back to paper\n"
        "ERROR crate 12 missing\n"
        "INFO  depot closed\n"
    )

    (tmp_path / "reminder").write_text(
        "Reminder: the scanner needs a new battery.\n"
    )


    errors = sweep(str(tmp_path))
    captured = capsys.readouterr()


    assert errors == 4

    assert "depot-mon.log      4 info   1 warn   1 error" in captured.out
    assert "depot-tue.log      4 info   0 warn   0 error" in captured.out
    assert "depot-wed.log      2 info   1 warn   3 error" in captured.out
    assert "4 errors across 3 files" in captured.out
    assert "worst file: depot-wed.log" in captured.out
    assert "reminder" not in captured.out

def test_sweep_worst_file_tie_tester(tmp_path, capsys):

    (tmp_path / "depot-mon.log").write_text(
        "INFO  depot opened\n"
        "ERROR crate 1 damaged\n"
        "ERROR crate 2 damaged\n"
        "ERROR crate 3 damaged\n"
        "INFO  depot closed\n"
    )

    (tmp_path / "depot-tue.log").write_text(
        "INFO  depot opened\n"
        "ERROR scanner offline\n"
        "ERROR scanner offline\n"
        "ERROR crate 12 missing\n"
        "INFO  depot closed\n"
    )

    errors = sweep(str(tmp_path))
    captured = capsys.readouterr()

    assert errors == 6
    assert "depot-mon.log      2 info   0 warn   3 error" in captured.out
    assert "depot-tue.log      2 info   0 warn   3 error" in captured.out
    assert "6 errors across 2 files" in captured.out
    assert "worst file: depot-mon.log" in captured.out

def test_main_success_no_errors(tmp_path):
    (tmp_path / "app.log").write_text("INFO server started\n")

    exit_code = main(["logsweep.py", str(tmp_path)])
    assert exit_code == 0


def test_main_success_with_errors(tmp_path):
    (tmp_path / "app.log").write_text("ERROR crash occurred\n")

    exit_code = main(["logsweep.py", str(tmp_path)])
    assert exit_code == 1


def test_main_usage_error(capsys):
    exit_code = main(["logsweep.py"])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "usage: logsweep.py <directory>" in captured.out

def test_main_not_a_directory(tmp_path, capsys):
    file_path = tmp_path / "notadir.txt"
    file_path.write_text("hi")
    exit_code = main(["logsweep.py", str(file_path)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "not a directory" in captured.out

def test_sweep_no_worst_line_when_zero_errors(tmp_path, capsys):
    (tmp_path / "thu.log").write_text("INFO ok\n")
    (tmp_path / "fri.log").write_text("INFO also ok\n")
    sweep(str(tmp_path))
    captured = capsys.readouterr()
    assert "worst file" not in captured.out

def test_sweep_sorts_filenames(tmp_path, capsys):
    (tmp_path / "thu.log").write_text("INFO thur\n")
    (tmp_path / "fri.log").write_text("INFO fri\n")
    sweep(str(tmp_path))
    out = capsys.readouterr().out
    assert out.index("fri.log") < out.index("thu.log")