from django.shortcuts import redirect


class RoleBasedRedirectMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Role based redirects.

        IMPORTANT:
        Do NOT redirect principals by matching only url_name,
        because it can break other flows (like homework -> student dashboard).
        """
        response = self.get_response(request)
        return response


