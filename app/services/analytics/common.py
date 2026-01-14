import os

from ...common.common import read_text_file


def load_compute_domain_usage_sql() -> str:
    """Функция загрузки SQL для вычисления статистики использования доменов.

    Returns:
        SQL текст запроса.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(base_dir, "sql", "compute_domain_usage.sql")
    return read_text_file(sql_path, encoding="utf-8")
