from datetime import datetime, timezone

import pytest

from bot.controllers.user_controllers import get_seconds_until_starting_mark


@pytest.mark.parametrize(
    "current_time, expected_seconds",
    [
        (datetime(2024, 1, 1, 13, 59, 59, tzinfo=timezone.utc), 1),
        (datetime(2024, 1, 1, 14, 0, 1, tzinfo=timezone.utc), 86399),
        (datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc), 7200),
        (datetime(2024, 1, 1, 15, 0, 0, tzinfo=timezone.utc), 82800),
    ],
)
def test_get_seconds_until_starting_mark(current_time, expected_seconds):
    current_hour = current_time.hour
    seconds = get_seconds_until_starting_mark(current_hour, current_time)
    assert seconds == expected_seconds
