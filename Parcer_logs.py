import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union

# Регулярное выражение для парсинга строк access.log
LOG_PATTERN = re.compile(r'(?P<ip>\S+) - - \[(?P<time>[^\]]+)\] "(?P<request>[A-Z]+ [^ ]+ [^"\\]+)" (?P<status>\d+) (?P<size>\d+|-) "(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)" (?P<duration>\d+)')


def parse_log_line(line: str) -> Union[Dict[str, Union[str, int, datetime]], None]:
    """Разбирает строку из лог-файла."""
    match = LOG_PATTERN.match(line)
    if match:
        data = match.groupdict()
        data['size'] = int(data['size']) if data['size'] != '-' else 0
        data['duration'] = int(data['duration'])
        data['time'] = datetime.strptime(data['time'], "%d/%b/%Y:%H:%M:%S %z")
        return data
    return None


def analyze_logs(file_path: Path) -> Dict[str, Union[int, Dict[str, int], List[Dict[str, Union[str, int]]]]]:
    """Анализирует один лог-файл и возвращает статистику."""
    stats = {
        'общее_количество_запросов': 0,
        'http_методы': {},
        'топ_ip': {},
        'самые_долгие_запросы': []
    }

    with file_path.open('r', encoding='utf-8') as file:
        for line in file:
            data = parse_log_line(line)
            if not data:
                continue

            # Общее количество запросов
            stats['общее_количество_запросов'] += 1

            # HTTP-методы
            method = data['request'].split()[0]
            stats['http_методы'][method] = stats['http_методы'].get(method, 0) + 1

            # Топ IP
            ip = data['ip']
            stats['топ_ip'][ip] = stats['топ_ip'].get(ip, 0) + 1

            # Самые долгие запросы
            request_info = {
                'метод': method,
                'url': data['request'].split()[1],
                'ip': ip,
                'длительность': data['duration'],
                'время': data['time'].isoformat()
            }
            stats['самые_долгие_запросы'].append(request_info)

    # Сортировка и ограничение результатов
    stats['топ_ip'] = sorted(stats['топ_ip'].items(), key=lambda x: x[1], reverse=True)[:3]
    stats['самые_долгие_запросы'] = sorted(stats['самые_долгие_запросы'], key=lambda x: x['длительность'], reverse=True)[:3]

    return stats


def save_results(results: Dict[str, Dict], output_dir: Path) -> None:
    """Сохраняет результаты анализа в JSON-файлы."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for log_file, stats in results.items():
        output_file = output_dir / f"{log_file}.json"
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(stats, f, indent=4, ensure_ascii=False)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Анализ лог-файлов доступа.")
    parser.add_argument("--output", default="результаты", help="Директория для сохранения результатов анализа.")
    args = parser.parse_args()

    log_file = Path("access.log")
    output_dir = Path(args.output)

    if not log_file.is_file():
        print(f"Ошибка: файл '{log_file}' не найден.")
        return

    results = {log_file.name: analyze_logs(log_file)}

    save_results(results, output_dir)

    for log_file, stats in results.items():
        print(f"Результаты анализа для {log_file}:")
        print(json.dumps(stats, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
