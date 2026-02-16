from types import SimpleNamespace

import pytest

from bot.controllers.processors import quiz_helpers
from enums import SlideType


class DummyEvent:
    def __init__(self) -> None:
        self.sent_text: str | None = None

    async def answer(self, *, text: str, **_kwargs) -> None:
        self.sent_text = text


@pytest.mark.anyio
async def test_answer_almost_right_reply_uses_fallback_and_reports_to_sentry(monkeypatch):
    quiz_helpers._missing_almost_right_answer_reply_reported.clear()

    event = DummyEvent()
    slide = SimpleNamespace(
        id=1,
        lesson_id=2,
        slide_type=SlideType.QUIZ_INPUT_WORD,
        almost_right_answer_reply=None,
    )

    async def fake_get_text_by_prompt(*, prompt: str, db_session) -> str:
        assert prompt == "missing_almost_right_answer_reply"
        assert db_session is not None
        return "fallback"

    captured: list[tuple[str, str | None]] = []

    def fake_capture_message(message: str, level: str | None = None):
        captured.append((message, level))
        return "event-id"

    monkeypatch.setattr(quiz_helpers, "get_text_by_prompt", fake_get_text_by_prompt)
    monkeypatch.setattr(quiz_helpers.sentry_sdk, "capture_message", fake_capture_message)

    await quiz_helpers.answer_almost_right_reply(event, slide, db_session=object())

    assert event.sent_text == "fallback"
    assert len(captured) == 1
    assert captured[0][1] == "warning"


@pytest.mark.anyio
async def test_answer_almost_right_reply_prefers_slide_reply_when_present(monkeypatch):
    quiz_helpers._missing_almost_right_answer_reply_reported.clear()

    event = DummyEvent()
    slide = SimpleNamespace(
        id=1,
        lesson_id=2,
        slide_type=SlideType.QUIZ_INPUT_WORD,
        almost_right_answer_reply="ok",
    )

    async def fake_get_text_by_prompt(*_args, **_kwargs) -> str:
        raise AssertionError("get_text_by_prompt should not be called")

    def fake_capture_message(*_args, **_kwargs):
        raise AssertionError("capture_message should not be called")

    monkeypatch.setattr(quiz_helpers, "get_text_by_prompt", fake_get_text_by_prompt)
    monkeypatch.setattr(quiz_helpers.sentry_sdk, "capture_message", fake_capture_message)

    await quiz_helpers.answer_almost_right_reply(event, slide, db_session=object())

    assert event.sent_text == "ok"


@pytest.mark.anyio
async def test_answer_almost_right_reply_dedupes_sentry_by_slide_id(monkeypatch):
    quiz_helpers._missing_almost_right_answer_reply_reported.clear()

    event = DummyEvent()
    slide = SimpleNamespace(
        id=1,
        lesson_id=2,
        slide_type=SlideType.QUIZ_INPUT_PHRASE,
        almost_right_answer_reply=None,
    )

    async def fake_get_text_by_prompt(*_args, **_kwargs) -> str:
        return "fallback"

    captured: list[tuple[str, str | None]] = []

    def fake_capture_message(message: str, level: str | None = None):
        captured.append((message, level))
        return "event-id"

    monkeypatch.setattr(quiz_helpers, "get_text_by_prompt", fake_get_text_by_prompt)
    monkeypatch.setattr(quiz_helpers.sentry_sdk, "capture_message", fake_capture_message)

    await quiz_helpers.answer_almost_right_reply(event, slide, db_session=object())
    await quiz_helpers.answer_almost_right_reply(event, slide, db_session=object())

    assert event.sent_text == "fallback"
    assert len(captured) == 1
