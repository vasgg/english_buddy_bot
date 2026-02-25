import pytest
from pydantic import ValidationError

from webapp.schemas.slide import EditMediaSlideData


def test_media_slide_requires_non_empty_media_id():
    with pytest.raises(ValidationError) as exc:
        EditMediaSlideData(media_id="   ")
    assert any(err["loc"] == ("media_id",) for err in exc.value.errors())


def test_media_slide_rejects_non_positive_delay():
    with pytest.raises(ValidationError) as exc:
        EditMediaSlideData(media_id="file-id", delay=0)
    assert any(err["loc"] == ("delay",) for err in exc.value.errors())


def test_media_slide_accepts_valid_data():
    payload = EditMediaSlideData(media_id="file-id", delay=1.5, keyboard_type=True)
    assert payload.media_id == "file-id"
    assert payload.delay == 1.5
    assert payload.keyboard_type is True
