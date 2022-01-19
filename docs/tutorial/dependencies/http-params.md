# HTTP Parameters in Dependencies

Your dependencies can depend on HTTP parameters.
For example, you can get a query parameter from within a dependency.
This can be useful to create reusable groups of parameters:

```python hl_lines="6-7 10"
--8<-- "docs_src/tutorial/dependencies/tutorial_005.py"
```

This applies to parameters as well as request bodies.
