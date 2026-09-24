import functools
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .services import (
    SettlementError,
    _serialize_result,
    get_course_detail,
    get_overview,
    get_referee_overview,
    revoke_result,
    submit_result,
)


def json_api(view):
    """统一把结算业务异常转换成 JSON 响应（视图层捕获，Django 中间件层无法拦截视图异常）。"""

    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except SettlementError as exc:
            return JsonResponse({"code": exc.code, "message": exc.message}, status=exc.status)
        except json.JSONDecodeError:
            return JsonResponse({"code": "bad_request", "message": "请求体不是合法的 JSON。"}, status=400)

    return wrapper


def health(_request):
    return JsonResponse({"status": "ok"})


def overview(_request):
    return JsonResponse(get_overview())


def _read_json(request):
    if not request.body:
        return {}
    payload = json.loads(request.body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise SettlementError("请求体必须是 JSON 对象。")
    return payload


@json_api
@require_http_methods(["GET"])
def course_detail(_request):
    return JsonResponse(get_course_detail())


@json_api
@csrf_exempt
@require_http_methods(["POST"])
def results_submit(request):
    payload = _read_json(request)
    result = submit_result(
        team_name=payload.get("teamName"),
        raw_sequence=payload.get("sequence"),
        raw_duration=payload.get("totalTime", payload.get("totalSeconds")),
    )
    return JsonResponse({"message": "成绩已提交并完成结算。", "result": _serialize_result(result)}, status=201)


@json_api
@require_http_methods(["GET"])
def results_overview(_request):
    return JsonResponse(get_referee_overview())


@json_api
@csrf_exempt
@require_http_methods(["POST"])
def results_revoke(request, result_id):
    payload = _read_json(request)
    result = revoke_result(result_id=result_id, reason=payload.get("reason", ""))
    return JsonResponse({"message": "成绩已撤销，队伍回到待结算。", "result": _serialize_result(result)})
