import base64
import binascii
import json
import uuid

from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import SelfieCapture


@csrf_exempt
@require_POST
def save_selfie(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        image_b64 = payload.get("image")
        if not image_b64:
            return JsonResponse({"error": "Missing image data."}, status=400)

        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]

        image_bytes = base64.b64decode(image_b64)
        if not request.session.session_key:
            request.session.create()

        capture = SelfieCapture(session_key=request.session.session_key)
        capture.image.save(
            f"sketch-{uuid.uuid4().hex}.jpg",
            ContentFile(image_bytes),
            save=True,
        )
        return JsonResponse(
            {
                "id": capture.id,
                "image_url": capture.image.url,
                "absolute_image_url": request.build_absolute_uri(capture.image.url),
                "created_at": capture.created_at.isoformat(),
            },
            status=201,
        )
    except (ValueError, json.JSONDecodeError, binascii.Error) as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception:
        return JsonResponse({"error": "Server error while saving image."}, status=500)
