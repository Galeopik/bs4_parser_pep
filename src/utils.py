import logging

# Импорт базового класса ошибок библиотеки request.
from requests import RequestException

from exceptions import ParserFindTagException


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}',
            stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, exc_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


def get_pep_status(soup):
    for tag in soup.find_all('dt'):
        if tag.get_text(strip=True).rstrip(':') == 'Status':
            status_tag = tag.find_next_sibling('dd')
            if status_tag:
                return status_tag.get_text(strip=True)
