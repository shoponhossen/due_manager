from django.contrib import admin
from .models import Customer, Product, Due, Deposit


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone_number", "user", "total_due_amount", "created_at")
    search_fields = ("name", "phone_number")
    list_filter = ("user", "created_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "quantity", "unit", "price", "created_at")
    search_fields = ("title",)
    list_filter = ("unit", "created_at")


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
