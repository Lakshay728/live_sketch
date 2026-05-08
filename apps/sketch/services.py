import base64
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class SketchResult:
    image_b64: str
    width: int
    height: int


class SketchService:
    MAX_WIDTH = 640
    MAX_HEIGHT = 480

    @staticmethod
    def _decode_image(frame_b64: str) -> np.ndarray:
        if "," in frame_b64:
            frame_b64 = frame_b64.split(",", 1)[1]
        image_bytes = base64.b64decode(frame_b64)
        np_buffer = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Invalid image payload.")
        return frame

    @staticmethod
    def _resize_for_realtime(frame: np.ndarray) -> np.ndarray:
        height, width = frame.shape[:2]
        if width <= SketchService.MAX_WIDTH and height <= SketchService.MAX_HEIGHT:
            return frame

        ratio = min(SketchService.MAX_WIDTH / width, SketchService.MAX_HEIGHT / height)
        new_w = int(width * ratio)
        new_h = int(height * ratio)
        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    @staticmethod
    def _to_sketch(frame: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        inverted = cv2.bitwise_not(gray)
        blurred = cv2.GaussianBlur(inverted, (21, 21), sigmaX=0, sigmaY=0)
        sketch = cv2.divide(gray, cv2.bitwise_not(blurred), scale=256.0)

        # Sharpen to bring out pencil-like line detail.
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sketch = cv2.filter2D(sketch, -1, kernel)

        # Improve local contrast for a more realistic sketch look.
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        sketch = clahe.apply(sketch)

        # Mild denoise to reduce grain while preserving edges.
        sketch = cv2.fastNlMeansDenoising(sketch, h=3)
        return sketch

    @classmethod
    def transform_frame(cls, frame_b64: str, jpeg_quality: int = 75) -> SketchResult:
        if not frame_b64:
            raise ValueError("Missing frame data.")

        frame = cls._decode_image(frame_b64)
        frame = cls._resize_for_realtime(frame)
        sketch = cls._to_sketch(frame)

        quality = max(40, min(95, int(jpeg_quality)))
        ok, encoded = cv2.imencode(
            ".jpg",
            sketch,
            [int(cv2.IMWRITE_JPEG_QUALITY), quality],
        )
        if not ok:
            raise ValueError("Unable to encode sketch image.")

        image_b64 = base64.b64encode(encoded.tobytes()).decode("ascii")
        height, width = sketch.shape[:2]
        return SketchResult(image_b64=image_b64, width=width, height=height)
