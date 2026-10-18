import logging
import re
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, MAIN_DOC_URL, MAIN_PEP_URL
from outputs import control_output, pep_output
from utils import find_tag, get_pep_results, get_soup

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
)

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


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')

    soup = get_soup(session=session, url=whats_new_url)

    sections_by_python = soup.select(
        '#what-s-new-in-python div.toctree-wrapper li.toctree-l1'
    )

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections_by_python, desc='Загрузка иформации: '):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        soup = get_soup(session=session, url=version_link)
        find_h1 = find_tag(soup, 'h1')
        find_dl = find_tag(soup, 'dl')
        dl_text = find_dl.text.replace('\n', ' ')

        results.append((version_link, find_h1.text, dl_text))

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
        raise LookupError(
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

    downloads_dir = BASE_DIR / 'downloads'  # Тест ожидает BASE_DIR
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

    for result in tqdm(results, desc='Проверка актульных статусов'):
        pep_url = urljoin(MAIN_PEP_URL, result['url'])
        soup = get_soup(session=session, url=pep_url)

        for tag in soup.find_all('dt'):
            if tag.get_text(strip=True).rstrip(':') == 'Status':
                status_tag = tag.find_next_sibling('dd')
                if status_tag:
                    actual_status = status_tag.get_text(strip=True)

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
    for warning in warnings:
        print(warning)
    pep_output(results)


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
        raise
    logging.info(ENDING_PARSER)


if __name__ == '__main__':
    main()
