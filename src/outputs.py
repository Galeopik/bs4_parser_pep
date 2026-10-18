import csv
import datetime as dt
import logging
from collections import Counter

from prettytable import PrettyTable

from constants import (BASE_DIR, DATETIME_FORMAT, ENCODING, OUTPUT_FILE,
                       OUTPUT_PRETTY)

SUCCESS_SAVE = 'Файл с результатами был сохранён: {path}'


def control_output(results, cli_args):
    output_functions = {
        OUTPUT_PRETTY: pretty_output,
        OUTPUT_FILE: file_output
    }
    output_function = output_functions.get(cli_args.output, default_output)
    output_function(results, cli_args)


def default_output(results, cli_args):
    for row in results:
        print(*row)


def pretty_output(results, cli_args):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    results_dir = BASE_DIR / 'results'  # Тест ожидает BASE_DIR
    results_dir.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    now_formatted = dt.datetime.now().strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now_formatted}.csv'
    file_path = results_dir / file_name
    with open(file_path, 'w', encoding=ENCODING) as f:
        csv.writer(f, dialect=csv.unix_dialect).writerows(results)
    logging.info(SUCCESS_SAVE.format(path=file_path))


def pep_output(results):
    status_counts = Counter(
        result['actual_status']
        for result in results
        if result['actual_status'] is not None
    )
    results_dir = BASE_DIR / 'results'  # Тест ожидает BASE_DIR
    results_dir.mkdir(exist_ok=True)
    results_path = results_dir / 'pep_statuses.csv'
    with open(
        results_path,
        'w',
        encoding='utf-8',
        newline=''
    ) as file:
        writer = csv.writer(file)
        writer.writerow(['Статус', 'Количество'])
        for status, count in sorted(status_counts.items()):
            writer.writerow([status, count])
        writer.writerow(['Total', sum(status_counts.values())])
    logging.info(SUCCESS_SAVE.format(path=results_path))
