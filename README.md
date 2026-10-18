# Парсер документации Python и статусов PEP

Консольное приложение на Python для сбора данных с официальных сайтов Python:

- список новых возможностей Python;
- список версий и их статусов;
- загрузка архива HTML-документации;
- проверка статусов PEP и сохранение сводной статистики в CSV.

## Возможности

Приложение поддерживает четыре режима работы:

| Режим | Назначение |
| --- | --- |
| `whats-new` | Собирает ссылки, заголовки и информацию об авторах статей из раздела [What’s New](https://docs.python.org/3/whatsnew/). |
| `latest-versions` | Получает версии Python и их текущие статусы. |
| `download` | Загружает архив HTML-документации Python в каталог `downloads/`. |
| `pep` | Проверяет статусы PEP и формирует статистику в `results/pep_statuses.csv`. |

Результаты режимов `whats-new` и `latest-versions` можно вывести в консоль, в красивую таблицу или сохранить в CSV.

## Требования

- Python 3.8 или новее;
- доступ к сети для обращения к `docs.python.org` и `peps.python.org`.

Основные библиотеки проекта: Beautiful Soup, Requests, Requests Cache, PrettyTable, tqdm и pytest.

## Установка

```git clone https://github.com/Galeopik/bs4_parser_pep.git```
```cd bs4_parser_pep```
```python -m venv venv```

Windows PowerShell:

```.\venv\Scripts\Activate.ps1```

Linux/macOS:

```source venv/bin/activate```

Установите зависимости:

```pip install -r requirements.txt```

## Запуск

Из корня проекта выполните:

```python src/main.py <режим>```

Примеры:

```python src/main.py whats-new```
```python src/main.py latest-versions --output pretty```
```python src/main.py latest-versions --output file```
```python src/main.py download```
```python src/main.py pep --clear-cache```

Доступные параметры:

- `-o pretty` — вывод результатов в таблицу;
- `-o file` — сохранение результатов в CSV;
- `-c` или `--clear-cache` — очистка HTTP-кэша перед запуском.

## Результаты и логи

- `results/` — CSV-файлы с результатами парсинга;
- `downloads/` — скачанные архивы документации;
- `logs/parser.log` — журнал работы приложения;
- `http_cache.sqlite` — кэш HTTP-запросов.

Режим `pep` сохраняет `results/pep_statuses.csv` с колонками «Статус» и «Количество», а также строкой `Total`.

## Структура проекта

```text
.
├── src/
│   ├── main.py       # сценарии парсинга и точка входа
│   ├── configs.py    # CLI-параметры и настройка логирования
│   ├── constants.py  # URL, пути и ожидаемые статусы
│   ├── outputs.py    # вывод в консоль, таблицу и CSV
│   ├── utils.py      # HTTP-запросы и поиск данных в HTML
│   └── exceptions.py # пользовательские исключения
├── tests/            # автоматические тесты
├── results/          # результаты работы
├── logs/             # логи
├── requirements.txt  # зависимости
└── pytest.ini        # настройки pytest
```

## Тестирование

```pytest```
```flake8 src tests```

Часть тестов использует моки HTTP-запросов. Тест `test_latest_versions` в исходном проекте помечен `@pytest.mark.skip()` и поэтому пропускается безусловно, пока этот декоратор не будет удалён.

## Автор
Белоусов Глеб Сергеевич

- GitHub: [Galeopik](https://github.com/Galeopik)
- Telegram: [Galeop](https://t.me/galeop)

