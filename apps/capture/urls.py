from django.urls import path

from .views import save_selfie


urlpatterns = [
    path("selfie/", save_selfie, name="save_selfie"),
]
