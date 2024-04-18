import pytest

from lesson_path import LessonPath


def test_lesson_empty_path_init():
    new_path = LessonPath('')
    assert new_path.path == []


def test_lesson_path_init():
    new_path = LessonPath('1.2.3')
    assert new_path.path == [1, 2, 3]


def test_add_slide():
    new_path = LessonPath('1.2.3')
    new_path.add_slide(1, 4)
    assert new_path.path == [4, 1, 2, 3]
    with pytest.raises(AssertionError):
        new_path.add_slide(1, 3)
        assert new_path.path == [1, 4, 2, 3]


def test_edit_slide():
    new_path = LessonPath('1.2.3')
    new_path.edit_slide(1, 100)
    assert new_path.path == [100, 2, 3]


def test_remove_slide():
    new_path = LessonPath('1.2.3')
    new_path.remove_slide(3)
    assert new_path.path == [1, 2]


def test_str():
    new_path = LessonPath('1.2.3')
    assert str(new_path) == '1.2.3'
    new_path = LessonPath('')
    assert str(new_path) == ''
