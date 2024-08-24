from django.utils.decorators import async_only_middleware


@async_only_middleware
def no_cache_middleware(get_response):
    async def middleware_async(request):
        response = await get_response(request)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    return middleware_async