import threading

request_local = threading.local()

def get_current_request():
    return getattr(request_local, 'request', None)

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_local.request = request
        response = self.get_response(request)
        request_local.request = None
        return response