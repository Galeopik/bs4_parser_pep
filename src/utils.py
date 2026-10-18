from bs4 import BeautifulSoup
from requests import RequestException

from constants import ENCODING, EXPECTED_STATUS
from exceptions import ParserFindTagException

ERROR_GET_RESPONSE = (
    'Возникла ошибка при загрузке страницы {url}'
    'Подрбный текст ошибки: {error}'
)
ERROR_TAG_MESSAGE = 'Не найден тег {tag} {attrs}'


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = ENCODING
        return response
    except RequestException as error:
        raise RequestException(
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
    if response is None:
        return
    soup = BeautifulSoup(response.text, features=features)
    return soup


def get_pep_results(section):
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
