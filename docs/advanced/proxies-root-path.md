# Setting the `root_path` for your Xpresso App

In most cases, when your app gets a request for `https://example.com/v1/api/app` the [URL path] will be `/v1/api/app`.
But sometimes if you are running behind a reverse proxy or some other network layer that does routing based on the path, some prefix of the path may be stripped.
For example, your proxy may be set up to direct traffic between `/v1/api/app` and `/v2/api/app`, and when it forwards the request to one of your applications, it may strip the `/v{1,2}/api` part of the path.
This means your application would _think_ that it is being called at `/app` when really the client is calling it at `/v1/api/app`.
Amongst other problems, this means that your OpenAPI docs won't work as intended: when Xpresso generates the Swagger client that your browser loads (usually `/docs`), it needs to inject it's own URL into it so that your browser can make a request back to the API to get the OpenAPI spec (usually `/openapi.json`).
If your app doesn't know about the `/v1/api` part of the path, it will tell the frontend (Swagger) to load `/openapi.json`, when it should have used `/v1/api/openapi.json` instead.

To get around these situations, the ASGI specification uses a parameter called `root_path`.
This is set by servers (like Uvicorn) or by your application.
To set this value in Xpresso, use the `root_path` parameter to `App`:

```python
--8<-- "docs_src/advanced/root_path.py"
```

[URL path]: https://sethmlarson.dev/blog/why-urls-are-hard-path-params-urlparse
