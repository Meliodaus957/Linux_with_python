import subprocess
import datetime
from collections import defaultdict
from typing import List, Dict, Any

# Функция для получения данных команды ps aux
def get_ps_aux_data() -> str:
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, check=True)
    return result.stdout

# Функция для парсинга данных команды ps aux
def parse_ps_aux(data: str) -> List[Dict[str, Any]]:
    lines = data.strip().split('\n')
    header, *processes = lines
    parsed_data = []

    for process in processes:
        parts = process.split(maxsplit=10)
        if len(parts) == 11:
            user, pid, cpu, mem, vsz, rss, tty, stat, start, time, command = parts
            parsed_data.append({
                'user': user,
                'cpu': float(cpu),
                'mem': float(mem),
                'command': command,
            })
    return parsed_data

# Функция для формирования отчета
def generate_report(parsed_data: List[Dict[str, Any]]) -> str:
    users = {entry['user'] for entry in parsed_data}
    total_processes = len(parsed_data)

    user_process_counts = defaultdict(int)
    total_cpu_usage = 0.0
    total_mem_usage = 0.0
    max_mem_process = None
    max_cpu_process = None

    for entry in parsed_data:
        user_process_counts[entry['user']] += 1
        total_cpu_usage += entry['cpu']
        total_mem_usage += entry['mem']

        if max_mem_process is None or entry['mem'] > max_mem_process['mem']:
            max_mem_process = entry

        if max_cpu_process is None or entry['cpu'] > max_cpu_process['cpu']:
            max_cpu_process = entry

    max_mem_process_name = max_mem_process['command'][:20] if max_mem_process else "N/A"
    max_cpu_process_name = max_cpu_process['command'][:20] if max_cpu_process else "N/A"

    report = (
        f"Отчёт о состоянии системы:\n"
        f"Пользователи системы: {', '.join(sorted(users))}\n"
        f"Процессов запущено: {total_processes}\n\n"
        f"Пользовательских процессов:\n"
    )

    for user, count in sorted(user_process_counts.items()):
        report += f"{user}: {count}\n"

    report += (
        f"\nВсего памяти используется: {total_mem_usage:.1f}%\n"
        f"Всего CPU используется: {total_cpu_usage:.1f}%\n"
        f"Больше всего памяти использует: {max_mem_process['mem'] if max_mem_process else 0.0}% ({max_mem_process_name})\n"
        f"Больше всего CPU использует: {max_cpu_process['cpu'] if max_cpu_process else 0.0}% ({max_cpu_process_name})\n"
    )

    return report

# Сохранение отчета в файл
def save_report(report: str) -> str:
    now = datetime.datetime.now()
    filename = now.strftime("%Y-%m-%d-%H:%M-scan.txt")
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(report)
    return filename

# Основная логика выполнения
if __name__ == "__main__":
    try:
        ps_aux_data = get_ps_aux_data()
        parsed_data = parse_ps_aux(ps_aux_data)
        report = generate_report(parsed_data)
        print(report)
        file_name = save_report(report)
        print(f"Отчёт сохранён в файл: {file_name}")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка выполнения команды ps aux: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
