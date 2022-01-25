# WebSockets

XPresso supports [WebSockets] via [Starlette's WebSocket support].
The only functionality added on top of Starlette's is the ability to inject HTTP parameters like headers:

```python
--8<-- "docs_src/advanced/websockets.py"
```

[WebSockets]: https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API
[Starlette's WebSocket support]: https://www.starlette.io/websockets/
