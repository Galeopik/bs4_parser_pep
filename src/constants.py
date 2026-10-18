from pathlib import Path

MAIN_DOC_URL = 'https://docs.python.org/3/'
MAIN_PEP_URL = 'https://peps.python.org/'
EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}
BASE_DIR = Path(__file__).parent
OUTPUT_PRETTY = 'pretty'
OUTPUT_FILE = 'file'
LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'parser.log'
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
ENCODING = 'utf-8'
SUCCESS_SAVE = 'Файл с результатами был сохранён: {path}'

# RESULTS_DIR = BASE_DIR / 'results'
# DOWNLOADS_DIR = BASE_DIR / 'downloads'
