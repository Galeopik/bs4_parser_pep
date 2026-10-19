import logging
import re
from collections import Counter
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL,
                       MAIN_PEP_URL)
from exceptions import ParserFindTagException
from outputs import control_output
from utils import find_tag, get_soup

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
)

ERROR_GET_SOUP = 'Не удалось загрузить статью: {url} {error}'
SUCCESS_DOWNLOAD = 'Архив был загружен и сохранён: {path}'
UNSECCESS_GET_STATUS = 'Не удалось получить статус: {url}'
MISMATCH_STATUS = (
    'Несовпадение статусов на странице {url}: '
    'статус в карточке - {actual_status}, '
    'ожидаемые статусы - {expected_statuses}'
)
STARTED_PARSER = 'Парсер запущен!'
ARGS_CMD = 'Аргументы командной строки: {args}'
ENDING_PARSER = 'Парсер завершил работу.'
ERROR_WORKING_PARSER = 'Ошибка во время работы парсера.'


def get_pep_results(section):
    """
    Функция вынесена, чтобы облегчить функцию pep
    И не вызвать ошибку flake8 'is too complex'
    """
    results = []

    for row in section.find_all('tr'):
        first_cell = row.find('td')
        link = row.find('a', href=True)
        if first_cell is None or link is None:
            continue

        status_code = first_cell.get_text(strip=True)[1:]
        results.append({
            'url': link['href'],
            'status_code': status_code,
            'expected_statuses': EXPECTED_STATUS.get(status_code),
        })
    return results


def get_actual_status_from_pep(session, pep_url):
    """
    Функция вынесена, чтобы облегчить функцию pep
    И не вызвать ошибку flake8 'is too complex'
    """
    soup = get_soup(session=session, url=pep_url)
    actual_status = None
    for tag in soup.find_all('dt'):
        if tag.get_text(strip=True).rstrip(':') == 'Status':
            status_tag = tag.find_next_sibling('dd')
            if status_tag:
                actual_status = status_tag.get_text(strip=True)
            break
    return actual_status


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')

    soup = get_soup(session=session, url=whats_new_url)

    version_links = soup.select(
        '#what-s-new-in-python div.toctree-wrapper li.toctree-l1 > a'
    )

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    exceptions = []
    for version_a_tag in tqdm(version_links, desc='Загрузка иформации: '):
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        try:
            soup = get_soup(session=session, url=version_link)
        except OSError as error:
            exceptions.append(ERROR_GET_SOUP.format(url=version_link,
                                                    error=error))
        find_h1 = find_tag(soup, 'h1')
        find_dl = find_tag(soup, 'dl')
        dl_text = find_dl.text.replace('\n', ' ')

        results.append((version_link, find_h1.text, dl_text))
    if exceptions:
        logging.exception('\n'.join(exceptions))
    return results


def latest_versions(session):
    soup = get_soup(session=session, url=MAIN_DOC_URL)
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebar'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise ParserFindTagException(
            'В боковой панели не найден список "All versions".'
        )
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (a_tag['href'], version, status)
        )
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    soup = get_soup(session=session, url=downloads_url)
    table = find_tag(soup, 'table', attrs={'class': 'docutils'})
    html_tag = find_tag(table, 'a', {'href': re.compile(r'.+docs-html\.zip$')})
    link = urljoin(downloads_url, html_tag['href'])
    filename = link.split('/')[-1]

    downloads_dir = BASE_DIR / 'downloads'  # НЕ МОГУ ПЕРЕНЕСТИ В КОНСТАНТУ!!!
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    response = session.get(link)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(SUCCESS_DOWNLOAD.format(path=archive_path))


def pep(session):
    soup = get_soup(session=session, url=MAIN_PEP_URL)
    section = find_tag(soup, 'section', attrs={'id': 'index-by-category'})
    results = get_pep_results(section)

    warnings = []
    exceptions = []

    for result in tqdm(results, desc='Проверка актульных статусов'):
        pep_url = urljoin(MAIN_PEP_URL, result['url'])
        try:
            soup = get_soup(session=session, url=pep_url)
        except OSError as error:
            exceptions.append(ERROR_GET_SOUP.format(url=pep_url,
                                                    error=error))
        actual_status = get_actual_status_from_pep(session, pep_url)
        result['actual_status'] = actual_status

        if actual_status is None:
            warnings.append(UNSECCESS_GET_STATUS.format(url=pep_url))
            continue

        expected_status = result['expected_statuses']
        if actual_status not in expected_status:
            warnings.append(MISMATCH_STATUS.format(
                url=pep_url,
                actual_status=actual_status,
                expected_statuses=list(expected_status))
            )
    if warnings:
        logging.warning('\n'.join(warnings))
    if exceptions:
        logging.exception('\n'.join(exceptions))
    status_counts = Counter(
        result['actual_status']
        for result in results
        if result['actual_status'] is not None
    )
    return [
        ('Статус', 'Количество'),
        *sorted(status_counts.items()),
        ('Total', sum(status_counts.values())),
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    configure_logging()
    logging.info(STARTED_PARSER)
    try:
        arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = arg_parser.parse_args()
        logging.info(ARGS_CMD.format(args=args))
        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()
        parser_mode = args.mode
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)
    except Exception:
        logging.exception(ERROR_WORKING_PARSER)
    logging.info(ENDING_PARSER)


if __name__ == '__main__':
    main()
