from django.db import models


class SelfieCapture(models.Model):
    session_key = models.CharField(max_length=64, db_index=True)
    image = models.ImageField(upload_to="selfies/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
