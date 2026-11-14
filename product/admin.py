from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "quantity", "unit", "price", "created_at")
    search_fields = ("title",)
    list_filter = ("unit", "created_at")
