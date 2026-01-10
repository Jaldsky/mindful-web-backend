"""Application package.

Важно: `app` импортируется в тестах, поэтому избегаем тяжёлых/побочных импортов на уровне пакета.
"""

try:
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:
    # `python-dotenv` — dev-зависимость; в некоторых окружениях (например, CI) может отсутствовать.
    pass
