from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DueViewSet

router = DefaultRouter()
router.register(r"", DueViewSet, basename="due")

urlpatterns = [
    path("", include(router.urls)),
]
