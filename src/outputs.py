import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import (DATETIME_FORMAT, ENCODING, OUTPUT_FILE, OUTPUT_PRETTY,
                       RESULTS_DIR, SUCCESS_SAVE)


def control_output(results, cli_args):
    OUTPUT_FUNCTIONS[cli_args.output](results, cli_args)


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
    RESULTS_DIR.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    now_formatted = dt.datetime.now().strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now_formatted}.csv'
    file_path = RESULTS_DIR / file_name
    with open(file_path, 'w', encoding=ENCODING) as f:
        csv.writer(f, dialect=csv.unix_dialect).writerows(results)
    logging.info(SUCCESS_SAVE.format(path=file_path))


OUTPUT_FUNCTIONS = {
    OUTPUT_PRETTY: pretty_output,
    OUTPUT_FILE: file_output,
    None: default_output
}
