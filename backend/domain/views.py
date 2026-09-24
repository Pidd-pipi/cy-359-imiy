from django.http import JsonResponse
from .services import get_overview

def health(_request):
    return JsonResponse({"status": "ok"})

def overview(_request):
    return JsonResponse(get_overview())
