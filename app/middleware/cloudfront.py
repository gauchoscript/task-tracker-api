from starlette.types import ASGIApp, Receive, Scope, Send

class CloudFrontForwardedProtoMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            for name, value in scope.get("headers", []):
                if name == b"cloudfront-forwarded-proto":
                    scope["scheme"] = value.decode("latin-1")
                    break
        await self.app(scope, receive, send)
