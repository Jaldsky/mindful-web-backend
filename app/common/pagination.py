from urllib.parse import urlencode
from typing import TypeVar
from fastapi import Request
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class PaginationUrlBuilder:
    """Помощник для построения ссылок пагинации."""

    @staticmethod
    def build_links(request: Request, pagination_data: T) -> T:
        """Создает копию объекта пагинации с заполненными ссылками next/prev.

        Args:
            request: Объект запроса FastAPI.
            pagination_data: Pydantic модель с полями page, total_pages, next, prev.

        Returns:
            Новый объект пагинации с обновленными ссылками.
        """
        new_pagination = pagination_data.model_copy()

        params = dict(request.query_params)
        base_url = request.url.path

        if new_pagination.page < new_pagination.total_pages:
            params["page"] = str(new_pagination.page + 1)
            new_pagination.next = f"{base_url}?{urlencode(params)}"
        else:
            new_pagination.next = None

        if new_pagination.page > 1:
            params["page"] = str(new_pagination.page - 1)
            new_pagination.prev = f"{base_url}?{urlencode(params)}"
        else:
            new_pagination.prev = None

        return new_pagination
