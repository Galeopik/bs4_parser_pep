import csv
from collections import Counter
import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from constants import BASE_DIR, MAIN_DOC_URL, MAIN_PEP_URL, EXPECTED_STATUS
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag, get_pep_status


logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
)


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div',
                           attrs={'class': 'toctree-wrapper compound'})
    sections_by_python = div_with_ul.find_all('li',
                                              attrs={'class': 'toctree-l1'})

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections_by_python, desc='Загрузка иформации: '):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)

        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        find_h1 = find_tag(soup, 'h1')
        find_dl = find_tag(soup, 'dl')
        dl_text = find_dl.text.replace('\n', ' ')

        results.append((version_link, find_h1.text, dl_text))

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebar'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception('Ничего не найдено')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (link, version, status)
        )
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    table = find_tag(soup, 'table', attrs={'class': 'docutils'})
    html_tag = find_tag(table, 'a', {'href': re.compile(r'.+docs-html\.zip$')})
    link = urljoin(downloads_url, html_tag['href'])
    filename = link.split('/')[-1]

    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    response = session.get(link)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    session = requests_cache.CachedSession()
    response = session.get(MAIN_PEP_URL)
    soup = BeautifulSoup(response.text, features='lxml')
    section = find_tag(soup, 'section', attrs={'id': 'index-by-category'})

    rows = section.find_all('tr')

    results = []

    for row in tqdm(rows, desc='Поиск всех статусов и типов'):
        first_cell = row.find('td')
        if first_cell is None:
            continue
        link = row.find('a', href=True)
        if link is None:
            continue
        url = link['href']
        preview_status = first_cell.get_text(strip=True)
        status_code = preview_status[1:]
        expected_statuses = EXPECTED_STATUS.get(status_code)
        results.append({
            'url': url,
            'status_code': status_code,
            'expected_statuses': expected_statuses
        })

    for result in tqdm(results, desc='Проверка актульных статусов'):
        pep_url = urljoin(MAIN_PEP_URL, result['url'])
        response = session.get(pep_url)
        soup = BeautifulSoup(response.text, features='lxml')

        actual_status = get_pep_status(soup)
        result['actual_status'] = actual_status

        if actual_status is None:
            logging.warning('Не удалось получить статус: %s', pep_url)
            continue

        expected_status = result['expected_statuses']
        if actual_status not in expected_status:
            logging.warning(
                'Несовпадение статусов на странице %s: '
                'статус в карточке — %s, ожидаемые статусы — %s',
                pep_url,
                actual_status,
                list(expected_statuses),
            )

    status_counts = Counter(
        result['actual_status']
        for result in results
        if result['actual_status'] is not None
    )
    results_dir = BASE_DIR / 'results'
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
    logging.info(f'Результат был загружен и сохранён: {results_path}')


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
