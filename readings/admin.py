from django.contrib import admin
from .models import ReadingType


@admin.register(ReadingType)
class ReadingTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_minutes', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
