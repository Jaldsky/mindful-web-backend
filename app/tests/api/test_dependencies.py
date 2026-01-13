import asyncio
from unittest import TestCase
from unittest.mock import patch, AsyncMock
from uuid import uuid4, uuid3, uuid5, uuid1, NAMESPACE_DNS
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_user_id_from_header, get_db_session
from app.db.session.provider import Provider
from app.services.events.exceptions import InvalidUserIdException


class TestGetUserIdFromHeader(TestCase):
    def _run_async(self, coro):
        """Вспомогательный метод для запуска асинхронного кода."""
        return asyncio.run(coro)

    def test_missing_header_generates_uuid4(self):
        """Если заголовок X-User-ID не передан - должен вернуться новый UUID4."""
        result = self._run_async(get_user_id_from_header(None))
        self.assertIsInstance(result, uuid4().__class__)
        self.assertEqual(result.version, 4)

    def test_valid_uuid4_returns_same_uuid(self):
        """Валидный UUID4 должен быть успешно распознан и возвращён как есть."""
        user_id = str(uuid4())
        result = self._run_async(get_user_id_from_header(user_id))
        self.assertEqual(str(result), user_id)
        self.assertEqual(result.version, 4)

    def test_uuid1_raises_http_400(self):
        """UUID1 (на основе MAC и времени) не поддерживается - ошибка InvalidUserIdException."""
        user_id = str(uuid1())
        with self.assertRaises(InvalidUserIdException) as cm:
            self._run_async(get_user_id_from_header(user_id))
        self.assertEqual(str(cm.exception), "X-User-ID must be a valid UUID4 string")

    def test_uuid3_raises_http_400(self):
        """UUID3 (хэш MD5) не поддерживается - ошибка InvalidUserIdException."""
        user_id = str(uuid3(NAMESPACE_DNS, "example.com"))
        with self.assertRaises(InvalidUserIdException) as cm:
            self._run_async(get_user_id_from_header(user_id))
        self.assertEqual(str(cm.exception), "X-User-ID must be a valid UUID4 string")

    def test_uuid5_raises_http_400(self):
        """UUID5 (хэш SHA-1) не поддерживается - ошибка InvalidUserIdException."""
        user_id = str(uuid5(NAMESPACE_DNS, "example.com"))
        with self.assertRaises(InvalidUserIdException) as cm:
            self._run_async(get_user_id_from_header(user_id))
        self.assertEqual(str(cm.exception), "X-User-ID must be a valid UUID4 string")

    def test_invalid_string_raises_http_400(self):
        """Невалидная строка (не UUID) вызывает InvalidUserIdException."""
        invalid_inputs = [
            "not-a-uuid",
            "123",
            "f47ac10b-58cc-4372-a567-0e02b2c3d47",
            "f47ac10b-58cc-4372-a567-0e02b2c3d479-extra",
            "",
        ]
        for invalid in invalid_inputs:
            with self.subTest(invalid=invalid):
                with self.assertRaises(InvalidUserIdException) as cm:
                    self._run_async(get_user_id_from_header(invalid))
                self.assertEqual(str(cm.exception), "X-User-ID must be a valid UUID4 string")

    def test_uppercase_uuid4_is_accepted(self):
        """UUID4 в верхнем регистре."""
        user_id = str(uuid4()).upper()
        result = self._run_async(get_user_id_from_header(user_id))
        self.assertEqual(str(result).upper(), user_id)
        self.assertEqual(result.version, 4)

    def test_uuid4_with_hyphens_is_accepted(self):
        """Стандартный UUID4 с дефисами - валиден."""
        uid = uuid4()
        result = self._run_async(get_user_id_from_header(str(uid)))
        self.assertEqual(result, uid)


class TestGetDbSession(TestCase):
    def _run_async(self, coro):
        """Вспомогательный метод для запуска асинхронного кода."""
        return asyncio.run(coro)

    @patch.object(Provider, "async_manager")
    def test_valid_session_returned(self, mock_manager_class):
        """Успешное получение сессии из менеджера."""
        mock_session = AsyncMock(spec=AsyncSession)

        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)

        mock_manager_class.get_session.return_value = mock_session_context

        async def test_coro():
            gen = get_db_session()
            session = await gen.__anext__()
            self.assertIs(session, mock_session)
            self.assertIsInstance(session, AsyncSession)

            with self.assertRaises(StopAsyncIteration):
                await gen.__anext__()

        self._run_async(test_coro())

    @patch.object(Provider, "async_manager")
    def test_session_is_yielded_only_once(self, mock_manager_class):
        """Генератор должен выдавать ровно одну сессию."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock()
        mock_manager_class.get_session.return_value = mock_session_context

        async def test_coro():
            gen = get_db_session()
            session1 = await gen.__anext__()
            self.assertIs(session1, mock_session)

            with self.assertRaises(StopAsyncIteration):
                await gen.__anext__()

        self._run_async(test_coro())

    def test_function_is_generator(self):
        """Функция должна быть асинхронным генератором."""
        gen = get_db_session()
        self.assertTrue(hasattr(gen, "__aiter__"))
        self.assertTrue(hasattr(gen, "__anext__"))
