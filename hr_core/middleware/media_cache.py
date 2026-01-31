# hr_core/middleware/media_cache.py

"""
Middleware to add cache headers to media files during development.

In production, your web server (nginx/Apache) should handle this via config.
This middleware helps prevent repeated image requests in Django's dev server.
"""

import hashlib


class MediaCacheMiddleware:
    """
    Add HTTP cache headers to /media/ responses.

    This is only useful during development with Django's runserver.
    In production, configure your web server to handle caching.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only add cache headers to media files
        if request.path.startswith('/media/'):
            # Cache for 1 week (604800 seconds)
            response['Cache-Control'] = 'public, max-age=604800, immutable'

            # Add ETag for conditional requests (304 Not Modified)
            if 'ETag' not in response and hasattr(response, 'content'):
                # Simple ETag based on path (could use content hash for accuracy)
                etag = hashlib.md5(request.path.encode()).hexdigest()[:16]
                response['ETag'] = f'"{etag}"'

            # Support If-None-Match for 304 responses
            if_none_match = request.META.get('HTTP_IF_NONE_MATCH', '').strip('"')
            response_etag = response.get('ETag', '').strip('"')

            if if_none_match and response_etag and if_none_match == response_etag:
                # Client has cached version, return 304 Not Modified
                response.status_code = 304
                response.content = b''
                # Remove content-related headers for 304
                response['Content-Length'] = '0'

        return response


# Optional: More aggressive caching for static files
class StaticCacheMiddleware:
    """
    Add cache headers to /static/ responses.
    Similar to MediaCacheMiddleware but for static files.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith('/static/'):
            # Cache static files for 1 year (since they should be versioned)
            response['Cache-Control'] = 'public, max-age=31536000, immutable'

        return response
