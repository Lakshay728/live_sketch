import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import SketchService


@csrf_exempt
@require_POST
def process_frame(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        frame_b64 = payload.get("frame")
        jpeg_quality = payload.get("quality", 75)
        result = SketchService.transform_frame(frame_b64, jpeg_quality=jpeg_quality)
        return JsonResponse(
            {
                "image": f"data:image/jpeg;base64,{result.image_b64}",
                "width": result.width,
                "height": result.height,
            }
        )
    except (ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)
