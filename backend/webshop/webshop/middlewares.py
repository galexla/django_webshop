from django.urls import reverse


def fix_frontend_bugs_middleware(get_response):
    def middleware(request):
        if request.path_info.startswith(
            '/api/'
        ) and not request.path_info.endswith('/'):
            request.path_info += '/'
            urls = [reverse('account:sign-in'), reverse('account:sign-up')]
            if request.path_info in urls:
                request.META['CONTENT_TYPE'] = 'application/json'
        response = get_response(request)
        return response

    return middleware
