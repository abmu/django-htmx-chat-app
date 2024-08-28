from django.urls import resolve
from django.utils.decorators import async_only_middleware

EXCLUDED_URLS = []


@async_only_middleware
def no_cache_middleware(get_response):
    async def middleware_async(request):
        response = await get_response(request)

        current_url_name = resolve(request.path_info).url_name
        
        if current_url_name not in EXCLUDED_URLS:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response

    return middleware_async