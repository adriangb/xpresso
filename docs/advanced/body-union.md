# Body Unions

You can accept a `Union` of bodies, which will be resolved by trying to deserialize each body and returning the first one that does not error.
If your bodies accept only specific content types (this is the default for json bodies but is opt-in for files) this will be used to discriminate the type.
If no bodies verify successfully, an error will be returned to the client.

```python
--8<-- "docs_src/advanced/body_union.py"
```
