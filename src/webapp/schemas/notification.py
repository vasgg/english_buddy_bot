from __future__ import annotations

from typing import Annotated, Any

from fastapi import UploadFile
from fastui.forms import FormFile
from pydantic import BaseModel, ConfigDict, Field, model_validator

from database.models.notification import NotificationCampaign, NotificationSegment
from enums import NotificationCampaignMode, NotificationCampaignStatus, NotificationTimeUnit, NotificationTimerAnchor


class NotificationCampaignTableSchema(BaseModel):
    id: int
    name: str = Field(title="Название")
    mode: str = Field(title="Режим")
    status: str = Field(title="Статус")
    updated: str = Field(title="Последняя обработка")
    preview_button: str = Field("👁", title=" ")
    edit_button: str = Field("✏️", title=" ")
    toggle_button: str = Field("▶️", title=" ")

    model_config = ConfigDict(from_attributes=True)


class NotificationCampaignForm(BaseModel):
    name: str = Field(
        title="Название уведомления",
        description="Внутреннее название кампании.",
    )
    message_text: str = Field(
        title="Текст уведомления",
        description="Сообщение, которое получит пользователь.",
        format="textarea",
        rows=6,
        cols=None,
    )
    mode: NotificationCampaignMode = Field(
        default=NotificationCampaignMode.FILTER,
        title="Формат отправки",
    )
    is_active: bool = Field(
        default=False,
        title="Кампания активна",
        description="Если включено, воркер начнет обработку кампании.",
    )
    is_silent: bool = Field(
        default=True,
        title="Тихая отправка",
        description="Отправлять сообщение без push-уведомления в Telegram.",
    )
    send_image_separately: bool = Field(
        default=False,
        title="Картинка отдельным сообщением",
        description=(
            "Если включено: картинка отправляется отдельным сообщением, текст — отдельным сообщением."
            " Если выключено и текст длиннее лимита caption, система всё равно отправит отдельно автоматически."
        ),
    )
    check_every_hours: int | None = Field(
        default=24,
        ge=1,
        title="Проверять каждые N часов (режим фильтра)",
    )
    timer_anchor: NotificationTimerAnchor | None = Field(
        default=None,
        title="Таймер: старт от",
    )
    timer_value: int | None = Field(
        default=None,
        ge=1,
        title="Таймер: отправлять через X",
    )
    timer_unit: NotificationTimeUnit | None = Field(
        default=None,
        title="Таймер: единица времени",
    )
    min_interval_value: int | None = Field(
        default=None,
        ge=1,
        title="Глобальный cooldown: X",
    )
    min_interval_unit: NotificationTimeUnit | None = Field(
        default=None,
        title="Глобальный cooldown: единица времени",
    )
    upload_new_picture: Annotated[UploadFile, FormFile(accept="image/*", max_size=10_000_000)] | None = Field(
        title="Картинка (опционально)",
        description="Изображение для уведомления.",
        default=None,
    )

    use_registration_age: bool = Field(default=False, title="Исключать по времени регистрации")
    registration_age_from_hours: int | None = Field(default=None, ge=0, title="Регистрация: от (часы)")
    registration_age_to_hours: int | None = Field(default=None, ge=0, title="Регистрация: до (часы)")

    use_inactivity: bool = Field(default=False, title="Исключать по времени от последней активности")
    inactivity_from_hours: int | None = Field(default=None, ge=0, title="Неактивность: от (часы)")
    inactivity_to_hours: int | None = Field(default=None, ge=0, title="Неактивность: до (часы)")

    use_last_lesson_completion: bool = Field(default=False, title="Исключать по времени от последнего урока")
    lesson_completion_age_from_hours: int | None = Field(default=None, ge=0, title="Последний урок: от (часы)")
    lesson_completion_age_to_hours: int | None = Field(default=None, ge=0, title="Последний урок: до (часы)")

    use_last_notification_age: bool = Field(default=False, title="Исключать по времени от последнего уведомления")
    last_notification_age_from_hours: int | None = Field(default=None, ge=0, title="Последнее уведомление: от (часы)")
    last_notification_age_to_hours: int | None = Field(default=None, ge=0, title="Последнее уведомление: до (часы)")

    use_has_paid_subscription: bool = Field(default=False, title="Исключать по платной подписке")
    has_paid_subscription: bool = Field(default=True, title="Платная подписка: есть")

    use_reminders_enabled: bool = Field(default=False, title="Исключать по личным уведомлениям (/reminders)")
    reminders_enabled: bool = Field(default=True, title="Личные уведомления: включены")

    use_completed_all_lessons: bool = Field(default=False, title="Исключать по флагу 'все уроки пройдены'")
    completed_all_lessons: bool = Field(default=True, title="Все уроки пройдены")

    model_config = ConfigDict(extra="allow", from_attributes=True)

    @model_validator(mode="after")
    def validate_form(self):
        if self.mode == NotificationCampaignMode.FILTER:
            if self.check_every_hours is None:
                raise ValueError("Для режима FILTER нужно указать check_every_hours")
        if self.mode == NotificationCampaignMode.TIMER:
            if self.timer_anchor is None or self.timer_value is None or self.timer_unit is None:
                raise ValueError("Для режима TIMER нужно указать таймер: anchor/value/unit")

        if (self.min_interval_value is None) ^ (self.min_interval_unit is None):
            raise ValueError("Для глобального cooldown укажите и значение, и единицу времени")

        _validate_range(self.registration_age_from_hours, self.registration_age_to_hours, "Регистрация")
        _validate_range(self.inactivity_from_hours, self.inactivity_to_hours, "Неактивность")
        _validate_range(self.lesson_completion_age_from_hours, self.lesson_completion_age_to_hours, "Последний урок")
        _validate_range(
            self.last_notification_age_from_hours, self.last_notification_age_to_hours, "Последнее уведомление"
        )
        return self


def _validate_range(value_from: int | None, value_to: int | None, name: str) -> None:
    if value_from is not None and value_to is not None and value_from > value_to:
        raise ValueError(f"{name}: 'от' не может быть больше 'до'")


def campaign_form_initial(campaign: NotificationCampaign, segment: NotificationSegment | None) -> dict[str, Any]:
    segment = segment or NotificationSegment(campaign_id=campaign.id)
    return {
        "name": campaign.name,
        "message_text": campaign.message_text,
        "mode": campaign.mode,
        "is_active": campaign.status == NotificationCampaignStatus.ACTIVE,
        "is_silent": bool(campaign.is_silent),
        "send_image_separately": bool(campaign.send_image_separately),
        "check_every_hours": campaign.check_every_hours,
        "timer_anchor": campaign.timer_anchor,
        "timer_value": campaign.timer_value,
        "timer_unit": campaign.timer_unit,
        "min_interval_value": campaign.min_interval_value,
        "min_interval_unit": campaign.min_interval_unit,
        "use_registration_age": bool(
            segment.registration_age_from_hours is not None or segment.registration_age_to_hours is not None
        ),
        "registration_age_from_hours": segment.registration_age_from_hours,
        "registration_age_to_hours": segment.registration_age_to_hours,
        "use_inactivity": bool(segment.inactivity_from_hours is not None or segment.inactivity_to_hours is not None),
        "inactivity_from_hours": segment.inactivity_from_hours,
        "inactivity_to_hours": segment.inactivity_to_hours,
        "use_last_lesson_completion": bool(
            segment.lesson_completion_age_from_hours is not None or segment.lesson_completion_age_to_hours is not None
        ),
        "lesson_completion_age_from_hours": segment.lesson_completion_age_from_hours,
        "lesson_completion_age_to_hours": segment.lesson_completion_age_to_hours,
        "use_last_notification_age": bool(
            segment.last_notification_age_from_hours is not None or segment.last_notification_age_to_hours is not None
        ),
        "last_notification_age_from_hours": segment.last_notification_age_from_hours,
        "last_notification_age_to_hours": segment.last_notification_age_to_hours,
        "use_has_paid_subscription": segment.has_paid_subscription is not None,
        "has_paid_subscription": bool(segment.has_paid_subscription),
        "use_reminders_enabled": segment.reminders_enabled is not None,
        "reminders_enabled": bool(segment.reminders_enabled),
        "use_completed_all_lessons": segment.completed_all_lessons is not None,
        "completed_all_lessons": bool(segment.completed_all_lessons),
    }
