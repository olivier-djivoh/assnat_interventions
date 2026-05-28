import threading

request_local = threading.local()

def get_current_request():
    return getattr(request_local, 'request', None)

def get_client_ip(request):
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    return None

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_local.request = request
        response = self.get_response(request)
        request_local.request = None
        return response