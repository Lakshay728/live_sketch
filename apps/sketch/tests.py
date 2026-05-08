import base64
import json

import cv2
import numpy as np
from django.test import Client, TestCase

from .services import SketchService


class SketchServiceTests(TestCase):
    def _sample_frame_b64(self) -> str:
        frame = np.full((120, 160, 3), 180, dtype=np.uint8)
        ok, encoded = cv2.imencode(".jpg", frame)
        self.assertTrue(ok)
        return base64.b64encode(encoded.tobytes()).decode("ascii")

    def test_transform_frame_returns_image(self):
        frame_b64 = self._sample_frame_b64()
        result = SketchService.transform_frame(frame_b64, jpeg_quality=70)
        self.assertTrue(result.image_b64)
        self.assertGreater(result.width, 0)
        self.assertGreater(result.height, 0)


class SketchApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        frame = np.full((90, 90, 3), 120, dtype=np.uint8)
        ok, encoded = cv2.imencode(".jpg", frame)
        self.assertTrue(ok)
        self.frame_data_url = "data:image/jpeg;base64," + base64.b64encode(
            encoded.tobytes()
        ).decode("ascii")

    def test_process_frame_endpoint(self):
        response = self.client.post(
            "/api/sketch/frame/",
            data=json.dumps({"frame": self.frame_data_url, "quality": 72}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("image", payload)
