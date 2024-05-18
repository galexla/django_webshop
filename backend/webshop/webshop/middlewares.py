from django.urls import reverse
from rest_framework.request import Request
from rest_framework.response import Response


def fix_frontend_bugs_middleware(get_response: callable) -> callable:
    """
    Add a trailing slash to API endpoints, change content type for the sign-in
    and sign-up pages. Thus fixing inconsitencies between swagger.yaml and the
    real frontend behaviour.

    :param get_response: A callable to get a response
    :type get_response: callable
    :return: A middleware function
    :rtype: callable
    """

    def middleware(request: Request) -> Response:
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
