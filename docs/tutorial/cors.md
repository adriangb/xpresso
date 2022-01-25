# CORS (Cross-Origin Resource Sharing)

XPresso does not itself provide any tooling for CORS protection, instead if just inherits it from Starlette.
For background, please see [Starlette's documentation on the matter] or [FastAPI's excellent summary].

This is just a quick example of what usage looks like in XPresso:

```python
--8<-- "docs_src/tutorial/cors.py"
```

[Starlette's documentation on the matter]: https://www.starlette.io/middleware/#corsmiddleware
[FastAPI's excellent summary]: https://fastapi.tiangolo.com/tutorial/cors/
