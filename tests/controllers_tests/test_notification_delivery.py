from notifications.delivery import send_with_single_retry, should_send_image_separately


def test_should_send_image_separately_when_forced():
    assert should_send_image_separately("short text", send_image_separately=True) is True


def test_should_send_image_separately_when_caption_too_long():
    assert should_send_image_separately("x" * 1025, send_image_separately=False) is True
    assert should_send_image_separately("x" * 100, send_image_separately=False) is False


async def test_send_with_single_retry_retries_once_on_transient_error():
    attempts = 0
    sleep_calls: list[float] = []

    async def sender() -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise TimeoutError("temporary")

    async def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    actual_attempts, error = await send_with_single_retry(sender, sleep=fake_sleep)

    assert error is None
    assert actual_attempts == 2
    assert attempts == 2
    assert len(sleep_calls) == 1


async def test_send_with_single_retry_does_not_retry_non_transient_error():
    attempts = 0

    async def sender() -> None:
        nonlocal attempts
        attempts += 1
        raise ValueError("fatal")

    actual_attempts, error = await send_with_single_retry(sender)

    assert isinstance(error, ValueError)
    assert actual_attempts == 1
    assert attempts == 1
