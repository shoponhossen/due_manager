from django.contrib import admin
from .models import Due, Deposit


@admin.register(Due)
class DueAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "amount", "date", "is_edited", "created_at")
    search_fields = ("customer__name",)
    list_filter = ("is_edited", "date")
    filter_horizontal = ("products",)


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "amount", "date", "created_at")
    search_fields = ("customer__name",)
    list_filter = ("date",)
