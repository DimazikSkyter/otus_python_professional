import filecmp
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Iterator
from assertpy import assert_that

from ru.otus.loganalyser.log_analyser import load_config_or_get_default, open_log, parse_log, LogFile, LogEntry

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src")))

def test_config_load(monkeypatch):
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_config.json"))
    monkeypatch.setattr(sys, "argv", ["script_name", "--config", config_path])
    config: Dict[str, Any] = load_config_or_get_default()

    assert_that(config).is_type_of(dict)
    assert_that(config).contains_key("LOG_DIR", "REPORT_DIR", "REPORT_SIZE")

    assert_that(config["LOG_DIR"]).is_equal_to("./resource")
    assert_that(config["REPORT_SIZE"]).is_greater_than(100)
    assert_that(config["ERROR_THRESHOLD"]).is_close_to(0.1, 0.01)

    print("\nConfig tested successfully.")

def test_logs_directory_is_empty():
    pass

def test_log_parser():
    log_path = Path(__file__).parent / "nginx_log.positive.txt"
    row_iterator = open_log(LogFile(path=log_path, ext="", date=datetime.now()))

    entries = list(parse_log(row_iterator, 1))

    assert len(entries) == 5, f"Expected 5 log entries, got {len(entries)}"

    expected = [
        LogEntry(host='1.199.168.112', url='/api/1/banners/?campaign=4198767',
                 time=datetime(2017, 6, 29, 3, 50, 28, tzinfo=timezone(timedelta(hours=3))),
                 method='GET', size='23765', request_time=0.461),
        LogEntry(host='1.141.86.192', url='/export/appinstall_raw/2017-06-30/',
                 time=datetime(2017, 6, 29, 3, 50, 29, tzinfo=timezone(timedelta(hours=3))),
                 method='GET', size='162', request_time=0.001),
        LogEntry(host='1.196.116.32', url='/api/v2/banner/24301798',
                 time=datetime(2017, 6, 29, 3, 50, 29, tzinfo=timezone(timedelta(hours=3))),
                 method='GET', size='1084', request_time=2.580),
        LogEntry(host='1.169.137.128', url='/api/v2/banner/15565644',
                 time=datetime(2017, 6, 29, 3, 50, 29, tzinfo=timezone(timedelta(hours=3))),
                 method='GET', size='1104', request_time=0.133),
        LogEntry(host='1.200.76.128', url='/api/1/campaigns/?id=5401863',
                 time=datetime(2017, 6, 29, 3, 50, 29, tzinfo=timezone(timedelta(hours=3))),
                 method='GET', size='646', request_time=0.146),
    ]

    for actual, expected_entry in zip(entries, expected):
        assert actual == expected_entry


def test_log_analyser(tmp_path):

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..\..\..\.."))
    print(f"\nBase dir {base_dir}")
    log_analyser = os.path.join(
        base_dir, "src", "ru", "otus", "loganalyser", "log_analyser.py"
    )
    resource_dir = os.path.join(base_dir, "resource")
    report_path = tmp_path / "report.html"
    log_path = os.path.join(resource_dir, "nginx-access-ui.log-20170630")
    reference_report = os.path.join(resource_dir, "report.html")

    subprocess.run(
        ["python", log_analyser, "--log-file", log_path, "--report-file", report_path],
        check=True,
    )

    # Проверка, что отчёт сгенерирован
    assert report_path.exists(), "Отчёт не был сгенерирован"

    # Сравниваем с эталонным отчётом
    assert filecmp.cmp(
        report_path, reference_report, shallow=False
    ), "Сгенерированный отчёт не совпадает с эталонным"
