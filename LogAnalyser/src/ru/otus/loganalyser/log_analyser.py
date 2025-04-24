#!/usr/bin/env python3

import re
import sys
import gzip
import json
import argparse
from datetime import datetime
from os import times
from pathlib import Path
from string import Template
from typing import Iterator, NamedTuple, List, Dict, Optional, Any
from collections import defaultdict
import statistics
import logging
import structlog

# Types
default_config = {
    "LOG_DIR": "/var/log/nginx",
    "REPORT_DIR": "./reports",
    "REPORT_SIZE": 1000,
    "ERROR_THRESHOLD": 0.1,
    "TEMPLATE": "report.html",
    "LOG_FILE": None,
    "PARSE_ERROR_THRESHOLD": 0.2,
}

LOG_LINE_RE = re.compile(
    r'''
    ^(?P<host>\d{1,3}(?:\.\d{1,3}){3})\s+            # IP
    (?P<token>\S+)\s+-\s+                              # второй токен + дефис
    \[(?P<time>[^\]]+)\]\s+                            # дата/время
    "(?P<method>GET|POST)\s+(?P<url>\S+)\s+HTTP/\d\.\d"\s+ #метод
    (?P<status>\d{3})\s+(?P<size>\d+)\s+               # статус и размер
    "(?P<referrer>[^"]*)"\s+                           # ссылка
    "(?P<agent>[^"]*)"\s+                              # user-agent
    "(?P<extra1>[^"]*)"\s*                             # 1-е доп. поле (без пробела!)
    "(?P<extra2>[^"]*)"\s*                             # 2-е доп. поле
    "(?P<extra3>[^"]*)"\s+                             # 3-е доп. поле (здесь есть пробел)
    (?P<request_time>\d+\.\d+)                         # request_time
    $
    ''',
    re.VERBOSE
)



class LogFile(NamedTuple):
    path: Path
    date: datetime
    ext: str


class LogEntry(NamedTuple):
    host: str
    url: str
    time: datetime
    method: str
    size: int
    request_time: float


def load_config_or_get_default() -> Dict[str, Any]:
    """
    Метод загружает конфиг, находящийся по локально или по пути, указанному в аргументе программы "config"
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    args, _ = parser.parse_known_args()
    config_path: Path = Path(args.config)
    defaults: Dict[str, Any] = default_config

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open() as f:
        cfg = json.load(f)

    merged = defaults.copy()
    merged.update(cfg)
    return merged


def setup_logging(log_path: Optional[str] = None):
    """
    Initialize structlog with JSON output
    """
    processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
    structlog.configure(processors=processors)
    if log_path:
        handler = logging.FileHandler(log_path)
    else:
        handler = logging.StreamHandler()


def find_last_log(log_dir: Path) -> Optional[LogFile]:
    """
    Find the most recent log file by name: nginx-access-ui.log-YYYYMMDD(.gz|.plain)
    """
    pattern = re.compile(r"nginx-access-ui\.log-(?P<date>\d{8})(?:\.gz)?$")
    latest: Optional[LogFile] = None
    for entry in log_dir.iterdir():
        m = pattern.match(entry.name)
        if not m:
            continue
        date = datetime.strptime(m.group("date"), "%Y%m%d")
        ext = ".gz" if entry.suffix == ".gz" else entry.suffix
        candidate = LogFile(path=entry, date=date, ext=ext)
        if latest is None or candidate.date > latest.date:
            latest = candidate
    return latest


def open_log(logfile: LogFile) -> Iterator[str]:
    """
    Open plain or gzip log file, yielding lines
    """
    opener = gzip.open if logfile.ext == ".gz" else open
    print(Path("nginx_log.positive.txt").absolute())
    with opener(logfile.path, "rt", encoding="utf-8") as f:
        for line in f:
            yield line




def parse_log(lines: Iterator[str], error_threshold: float) -> Iterator[LogEntry]:
    """

    Yield LogEntry for each parsed line; track parse errors and abort if too many.
    """
    total = 0
    errors = 0
    for line in lines:
        total += 1
        m = LOG_LINE_RE.search(line)
        if not m:
            errors += 1
            continue
        yield LogEntry(
            host=m.group("host"),
            url=m.group("url"),
            time=datetime.strptime(m.group("time"), "%d/%b/%Y:%H:%M:%S %z") if m.group("time") != "-" else None,
            method=m.group("method"),
            size=m.group("size"),
            request_time=float(m.group("request_time")))
    if total and errors / total > error_threshold:
        structlog.get_logger().error(
            "High parse error rate", total=total, errors=errors
        )
        raise RuntimeError("Parse errors exceed threshold")

def none_if_dash(value: str):
    return None if value == "-" else value

def process_entries(
    entries: Iterator[LogEntry],
    report_size: int
) -> List[Dict[str, any]]:
    """
    Compute statistics for each URL and return top N by time_sum
    """
    stats: Dict[str, List[float]] = defaultdict(list)
    for entry in entries:
        stats[entry.url].append(entry.request_time)
    total_count = sum(len(v) for v in stats.values())
    total_time = sum(sum(v) for v in stats.values())

    report = []
    for url, times in stats.items():
        times.sort()
        count = len(times)
        time_sum = sum(times)
        report.append(
            {
                "url": url,
                "count": count,
                "count_perc": count / total_count,
                "time_sum": time_sum,
                "time_perc": time_sum / total_time,
                "time_avg": time_sum / count,
                "time_max": max(times),
                "time_med": statistics.median(times),
            }
        )
    report.sort(key=lambda x: x["time_sum"], reverse=True)
    return report[:report_size]


def render_report(report_data: List[Dict], template_path: Path, output_path: Path):
    """
    Render the HTML report from template and JSON data
    """
    tpl = Template(template_path.read_text(encoding="utf-8"))
    table_json = json.dumps(report_data)
    html = tpl.safe_substitute(table_json=table_json)
    output_path.write_text(html, encoding="utf-8")


def main():
    config = load_config_or_get_default()

    setup_logging(config.get("LOG_FILE"))
    logger = structlog.get_logger()
    log_dir = Path(config["LOG_DIR"])
    last = find_last_log(log_dir)
    if not last:
        logger.info("No logs to process")
        return

    report_file = (
        Path(config["REPORT_DIR"]) / f"report-{last.date.strftime('%Y.%m.%d')}.html"
    )
    if report_file.exists():
        logger.info("Report already exists", report=str(report_file))
        return

    lines = open_log(last)
    parsed = parse_log(lines, config["PARSE_ERROR_THRESHOLD"])
    report_data = process_entries(parsed, config["REPORT_SIZE"])
    render_report(report_data, Path(config["TEMPLATE"]), report_file)

    logger.info("Report generated successfully", report=str(report_file))


if __name__ == "__main__":
    main()
