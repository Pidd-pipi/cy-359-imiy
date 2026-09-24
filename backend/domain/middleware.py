import json  # noqa: F401  (保留以便后续扩展结构化日志)
import logging

from django.http import JsonResponse

logger = logging.getLogger("lporienteering")


class JsonErrorMiddleware:
    """把 /api/ 下由框架生成的 404/405/500 响应统一包装成 JSON。

    视图主动抛出的业务异常在视图装饰器 json_api 中处理；
    Django 会把未捕获的视图异常在进入中间件链前转换成 500 响应，
    因此中间件这里只做响应后处理。
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith("/api/") and response.status_code in (404, 405, 500):
            if response.status_code == 404:
                message = "接口不存在。"
            elif response.status_code == 405:
                message = "不支持该请求方法。"
            else:
                logger.error("Unhandled server error for %s", request.path)
                message = "服务内部错误，请稍后重试。"
            return JsonResponse({"code": "http_error", "message": message}, status=response.status_code)
        return response
