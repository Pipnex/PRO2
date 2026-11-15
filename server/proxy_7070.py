import asyncio
from aiohttp import web, ClientSession

async def proxy_handler(request):
    target_url = f"http://127.0.0.1:8899{request.rel_url}"
    try:
        async with ClientSession() as session:
            body = await request.read()
            headers = {k: v for k, v in request.headers.items() if k.lower() not in ('host', 'content-length')}
            async with session.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=body if body else None,
                allow_redirects=False
            ) as resp:
                resp_body = await resp.read()
                excluded_headers = {'content-encoding', 'transfer-encoding', 'connection'}
                resp_headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded_headers}
                return web.Response(body=resp_body, status=resp.status, headers=resp_headers)
    except Exception as e:
        return web.Response(text=f"Proxy error: {e}", status=502)

app = web.Application()
app.router.add_route('*', '/{tail:.*}', proxy_handler)

if __name__ == '__main__':
    print("Proxy 7070 -> 8899 running...")
    web.run_app(app, host='127.0.0.1', port=7070)
