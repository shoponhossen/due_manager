from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone_number", "user", "total_due_amount", "created_at")
    search_fields = ("name", "phone_number")
    list_filter = ("user", "created_at")
