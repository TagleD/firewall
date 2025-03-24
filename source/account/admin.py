from django.contrib import admin
from django.contrib.auth import get_user_model


# Register your models here.
@admin.register(get_user_model())
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'is_superuser',
    )
    list_display_links = (
        'id',
        'username',
        'is_superuser',
    )