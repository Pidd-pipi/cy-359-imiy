import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .errors import AppError
from .models import Route
from .services import (
    get_referee_overview,
    list_routes,
    revoke_result,
    submit_result,
)

logger = logging.getLogger("lporienteering")


def health(_request):
    return JsonResponse({"status": "ok"})


def _json_body(request):
    if not request.body:
        return {}
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise AppError("请求体必须是合法 JSON")
    if not isinstance(payload, dict):
        raise AppError("请求体必须是 JSON 对象")
    return payload


def _integer_param(request, name):
    raw = request.GET.get(name)
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise AppError(f"参数 {name} 必须为整数")


def handle_api(view_func):
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except AppError as exc:
            return JsonResponse(
                {"error": exc.error_code, "message": exc.message, **exc.payload},
                status=exc.status_code,
            )
        except Exception:  # noqa: BLE001 - 兜底，避免堆栈直接暴露
            logger.exception("Unhandled error in %s", view_func.__name__)
            return JsonResponse(
                {"error": "internal_error", "message": "服务器内部错误"}, status=500
            )

    wrapper.__name__ = view_func.__name__
    return wrapper


@handle_api
@require_http_methods(["GET"])
def routes(_request):
    return JsonResponse({"routes": list_routes()})


@handle_api
@require_http_methods(["GET"])
def overview(request):
    route_id = _integer_param(request, "route")
    return JsonResponse(get_referee_overview(route_id=route_id))


@handle_api
@csrf_exempt
@require_http_methods(["POST"])
def submit(request):
    payload = _json_body(request)

    route_id = payload.get("routeId")
    if isinstance(route_id, bool) or not isinstance(route_id, int):
        raise AppError("routeId 必须为整数")
    if not Route.objects.filter(pk=route_id).exists():
        raise AppError("线路不存在", status_code=404)

    result = submit_result(
        route_id=route_id,
        team_name=payload.get("teamName"),
        submitted_sequence=payload.get("submittedSequence"),
        total_seconds=payload.get("totalSeconds"),
    )
    return JsonResponse({"record": result}, status=201)


@handle_api
@csrf_exempt
@require_http_methods(["POST"])
def revoke(request, result_id):
    payload = _json_body(request)
    result = revoke_result(result_id=result_id, reason=payload.get("reason", ""))
    return JsonResponse({"record": result})
