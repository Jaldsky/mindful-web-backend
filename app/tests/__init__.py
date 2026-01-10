try:
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:
    # `python-dotenv` — dev-зависимость; тесты не должны падать из-за её отсутствия.
    pass
