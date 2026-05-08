import base64
import json

import cv2
import numpy as np
from django.test import Client, TestCase

from .models import SelfieCapture


class CaptureApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        frame = np.full((100, 100, 3), 200, dtype=np.uint8)
        ok, encoded = cv2.imencode(".jpg", frame)
        self.assertTrue(ok)
        self.image_data_url = "data:image/jpeg;base64," + base64.b64encode(
            encoded.tobytes()
        ).decode("ascii")

    def test_save_selfie_endpoint(self):
        response = self.client.post(
            "/api/capture/selfie/",
            data=json.dumps({"image": self.image_data_url}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(SelfieCapture.objects.count(), 1)
        payload = response.json()
        self.assertIn("image_url", payload)
