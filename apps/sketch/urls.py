from django.urls import path

from .views import process_frame


urlpatterns = [
    path("frame/", process_frame, name="process_frame"),
]
