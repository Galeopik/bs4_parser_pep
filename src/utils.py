from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException

ERROR_GET_RESPONSE = (
    'Возникла ошибка при загрузке страницы {url}'
    'Подрбный текст ошибки: {error}'
)
ERROR_TAG_MESSAGE = 'Не найден тег {tag} {attrs}'


def get_response(session, url, encoding='utf-8'):
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except RequestException as error:
        raise OSError(
            ERROR_GET_RESPONSE.format(url=url, error=error)
        )


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        raise ParserFindTagException(
            ERROR_TAG_MESSAGE.format(tag=tag, attrs=attrs)
        )
    return searched_tag


def get_soup(session, url, features='lxml'):
    response = get_response(session, url)
    return BeautifulSoup(response.text, features=features)
