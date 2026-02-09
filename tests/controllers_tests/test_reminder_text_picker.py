import bot.controllers.user_controllers as user_controllers


def _reset_picker_state() -> None:
    user_controllers._reminder_text_picker.source_key = None
    user_controllers._reminder_text_picker.pool.clear()


def test_pick_reminder_text_cycles_without_repeats(monkeypatch):
    _reset_picker_state()

    monkeypatch.setattr(user_controllers.random, 'choice', lambda seq: seq[0])

    variants = ['a', 'b', 'c']
    assert user_controllers._pick_reminder_text(variants, reminder_text_fallback='fallback') == 'a'
    assert user_controllers._pick_reminder_text(variants, reminder_text_fallback='fallback') == 'b'
    assert user_controllers._pick_reminder_text(variants, reminder_text_fallback='fallback') == 'c'
    assert user_controllers._pick_reminder_text(variants, reminder_text_fallback='fallback') == 'a'


def test_pick_reminder_text_falls_back_when_variants_empty():
    _reset_picker_state()

    assert user_controllers._pick_reminder_text([], reminder_text_fallback='fallback') == 'fallback'


def test_pick_reminder_text_ignores_blank_variants(monkeypatch):
    _reset_picker_state()

    monkeypatch.setattr(user_controllers.random, 'choice', lambda seq: seq[0])

    variants = [' ', '', '\n', 'a']
    assert user_controllers._pick_reminder_text(variants, reminder_text_fallback='fallback') == 'a'
    assert user_controllers._pick_reminder_text(variants, reminder_text_fallback='fallback') == 'a'


def test_pick_reminder_text_resets_when_variants_change(monkeypatch):
    _reset_picker_state()

    monkeypatch.setattr(user_controllers.random, 'choice', lambda seq: seq[0])

    assert user_controllers._pick_reminder_text(['a', 'b'], reminder_text_fallback='fallback') == 'a'
    assert user_controllers._pick_reminder_text(['x', 'y'], reminder_text_fallback='fallback') == 'x'

