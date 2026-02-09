import pytest
from pydantic import ValidationError

from webapp.schemas.slide import EditQuizInputPhraseSlideData, EditQuizInputWordSlideData


def test_quiz_input_word_requires_reply_when_almost_answers_present():
    with pytest.raises(ValidationError) as exc:
        EditQuizInputWordSlideData(
            text="a_b",
            right_answers="x",
            almost_right_answers="foo|bar",
        )

    assert any(err["loc"] == ("almost_right_answer_reply",) for err in exc.value.errors())


def test_quiz_input_phrase_requires_reply_when_almost_answers_present():
    with pytest.raises(ValidationError) as exc:
        EditQuizInputPhraseSlideData(
            text="translate me",
            right_answers="x|y",
            almost_right_answers="foo|bar",
        )

    assert any(err["loc"] == ("almost_right_answer_reply",) for err in exc.value.errors())


def test_quiz_input_word_allows_missing_reply_when_almost_answers_blank():
    EditQuizInputWordSlideData(
        text="a_b",
        right_answers="x",
        almost_right_answers=" |  | ",
    )


def test_quiz_input_phrase_allows_missing_reply_when_no_almost_answers():
    EditQuizInputPhraseSlideData(
        text="translate me",
        right_answers="x|y",
    )

