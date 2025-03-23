from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
    )

    PAGINATION_CHOICES = [
        (25, '25 records per page'),
        (50, '50 records per page'),
        (75, '75 records per page'),
        (100, '100 records per page'),
    ]

    pagination_count = models.PositiveSmallIntegerField(
        choices=PAGINATION_CHOICES,
        default=50,
        verbose_name="Number of records per page",
    )