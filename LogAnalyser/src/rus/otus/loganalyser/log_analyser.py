#!/usr/bin/env python3

import argparse
import gzip
import json
import logging
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from os import times
from pathlib import Path
from string import Template
from typing import (IO, Any, Callable, Dict, Iterator, List, NamedTuple,
                    Optional, Tuple, cast)

import structlog
from packaging.tags import logger

ENCODING_UTF8 = "utf-8"
REPORT_DIR_KEY = "REPORT_DIR"
BASE_DIR = Path(__file__).resolve().parents[4]

LOG_LINE_RE = re.compile(
    r"""
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
    """,
    re.VERBOSE,
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

    default_config_path = Path("config.json")
    user_config_path = Path(args.config)

    if not default_config_path.exists():
        raise FileNotFoundError(f"Default config file not found: {default_config_path}")

    # Загружаем дефолтный конфиг
    with default_config_path.open() as f:
        defaults = json.load(f)

    merged = defaults.copy()

    if user_config_path.exists() and user_config_path != default_config_path:
        with user_config_path.open() as f:
            user_cfg = json.load(f)
        merged.update(user_cfg)

    return merged


def setup_logging(config: Dict[str, Any]):
    """
    Инициализируем логгер
    :param config: Конфигурация исполнения программы
    :return:
    """
    log_path_template = config.get("LOGGER_OUTPUT_FILE")
    handler: logging.Handler
    if log_path_template:
        today = datetime.now().strftime("%Y.%m.%d")
        log_path = BASE_DIR / log_path_template.replace("{{date}}", today)
        log_path = Path(log_path)

        log_path.parent.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(log_path)
    else:
        handler = logging.StreamHandler(sys.stdout)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers = [handler]

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    init_logger = structlog.get_logger()
    init_logger.info("Logger successfully initialized.")
    return init_logger


def find_last_log(config: Dict[str, Any], logger) -> Optional[LogFile]:
    """
    Ищем последний файл соответствующий шаблону
    """
    log_dir: Path = BASE_DIR / config["LOG_DIR"]
    report_dir: Path = BASE_DIR / config[REPORT_DIR_KEY]
    pattern = re.compile(r"nginx-access-ui\.log-(?P<date>\d{8})(?:\.gz)?$")
    logger.info("Try to find last log file.")

    latest: Optional[LogFile] = None
    for entry in log_dir.iterdir():
        if not entry.is_file():
            continue
        m = pattern.match(entry.name)
        if not m:
            continue
        date = datetime.strptime(m.group("date"), "%Y%m%d")
        ext = ".gz" if entry.suffix == ".gz" else entry.suffix
        candidate = LogFile(path=entry, date=date, ext=ext)
        if latest is None or candidate.date > latest.date:
            latest = candidate
    if latest is None:
        return None

    logger.info("File found successfully. Try to check report already exists.")
    report_filename = f"report-{latest.date.strftime('%Y.%m.%d')}.html"
    report_path = report_dir / report_filename
    if not report_path.exists():
        return latest

    return None


def open_log(logfile: LogFile, logger) -> Iterator[str]:
    """
    Открытие файла как gz, так и тектосового
    """
    opener = cast(Callable[..., IO[Any]], gzip.open if logfile.ext == ".gz" else open)
    logger.info(f"Try to open file {logfile.path}")

    try:
        f = opener(logfile.path.as_posix(), "rt", encoding=ENCODING_UTF8)
    except OSError:
        logger.exception(f"Failed to open file {logfile.path}")
        return
    except UnicodeDecodeError:
        logger.exception(f"Failed to decode file {logfile.path}")
        return

    try:
        with f:
            for line in f:
                yield line
    except (OSError, UnicodeDecodeError):
        logger.exception(f"Error while file is reading {logfile.path}")
        return


def check_actual_date():
    pass


def parse_log(
    lines: Iterator[str], config: Dict[str, Any], logger
) -> Iterator[LogEntry]:
    """
    Обработка лога
    """
    error_threshold = config.get("PARSE_ERROR_THRESHOLD")
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
            time=(
                datetime.strptime(m.group("time"), "%d/%b/%Y:%H:%M:%S %z")
                if m.group("time") and m.group("time") != "-"
                else datetime.min
            ),
            method=m.group("method"),
            size=(
                int(m.group("size"))
                if m.group("size") and m.group("size").isdigit()
                else 0
            ),
            request_time=float(m.group("request_time")),
        )
    if error_threshold is not None and total and errors / total > error_threshold:
        logger.error("High parse error rate", total=total, errors=errors)
        raise RuntimeError("Parse errors exceed threshold")


def none_if_dash(value: str):
    return None if value == "-" else value


def process_entries(
    entries: Iterator[LogEntry], config: Dict[str, Any], logger
) -> List[Dict[str, Any]]:
    """
    Высчитываем статистику на основе LogEntry генератора
    :param entries: генератор
    :param config: Конфиг исполнения программы
    :param logger: логгер исполнения
    :return:
    """
    report_size: int = config.get("REPORT_SIZE") or 1000
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
    report.sort(key=lambda x: cast(float, x["time_sum"]), reverse=True)
    return report[:report_size]


def render_report(report_data: List[Dict], config: Dict[str, Any], logger) -> str:
    """
    Генерация отчета на основании шаблона и данных
    """
    try:
        template_path: Path = BASE_DIR / config["TEMPLATE"]
        logger.info("Try to render report.")
        tpl = Template(template_path.read_text(encoding=ENCODING_UTF8))
        table_json = json.dumps(report_data)
        return tpl.safe_substitute(table_json=table_json)
    except Exception as e:
        logger.exception("Failed to render report.")
        raise e


def save_rendered_report(
    rendered_report: Tuple[str, str], config: Dict[str, Any], logger
):
    """
    Сохраняет сформированный отчет в директорию отчетов
    :param rendered_report: пара из имени файла и срендеренного отчета.
    :param config: Конфигурация исполнения программы
    :param logger: логгер исполнения
    :return: Ничего не возвращает
    """
    filename, html = rendered_report
    output_path: Path = BASE_DIR / config[REPORT_DIR_KEY] / filename
    logger.info(f"Try to save file {output_path}")
    output_path.write_text(html, encoding=ENCODING_UTF8)


def main():
    config = load_config_or_get_default()
    logger = setup_logging(config)
    last_log_file = find_last_log(config, logger)

    if not last_log_file:
        logger.info("No logs to process")
        return

    lines = open_log(last_log_file, logger)
    parsed = parse_log(lines, config, logger)
    report_data = process_entries(parsed, config, logger)
    rendered_report = render_report(report_data, config, logger)
    save_rendered_report(
        (f"report-{last_log_file.date.strftime('%Y.%m.%d')}.html", rendered_report),
        config,
        logger,
    )

    logger.info(
        f"Report generated and saved successfully for day {last_log_file.date.strftime('%Y.%m.%d')}"
    )


if __name__ == "__main__":
    main()
