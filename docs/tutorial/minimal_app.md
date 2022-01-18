# Getting started: a minimal Xpresso app

Start by making a file called `main.py` and fill out the following code:

```python
--8<-- "docs_src/tutorial/minimal_app.py"
```

What we've done here so far is:

1. Create an endpoint function.
1. Create a PathItem. A PathItem represents a unique HTTP resource, and can have several http methods attached to it.
1. Bind our endpoint function to the PathItem's GET method.
1. Create an `App` instance that uses the PathItem.

This is actually all we need, so you can run this using Uvicorn:

```python
uvicorn main:app
```

Now navigate to [http://localhost:8000/](http://localhost:8000/) and you should see `{"message": "Hello World"}` on your screen.

## Interactive Swagger Docs

You can also navigate to [http://localhost:8000/docs](http://localhost:8000/docs) to see the OpenAPI docs, served via [Swagger UI].

!!! info "Info"
    Swagger UI is a collection of HTML and scripts that serve as a frontend to an OpenAPI specification.
    Swagger gives you an interactive UI where you can send requests and get responses from your backend, all based on the OpenAPI specification that Xpresso automatically builds for you.

Since we didn't give Xpresso much info on the endpoint function's return value (it is implicitly `None`) and there is no request body, there isn't much information in OpenAPI.
In later chapters, you will see how we can give Xpresso more information.

[Swagger UI]: https://swagger.io/tools/swagger-ui/
