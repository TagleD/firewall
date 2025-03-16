from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Report(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )  # Владелец отчета
    name = models.CharField(
        max_length=255,
    )  # Название отчета
    created_at = models.DateTimeField(
        auto_now_add=True,
    )  # Дата создания

    def __str__(self):
        return f"{self.name} (ID: {self.id})"
