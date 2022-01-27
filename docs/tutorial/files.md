# Files

You can read the request body directly into a file or bytes.
This will read the data from the top level request body, and can only support 1 file.
To receive multiple files, see the [multipart/form-data documentation].

```python
--8<-- "docs_src/tutorial/file.py"
```

!!! note "Note"
    `UploadFile` is a class provided by Starlette that buffers the data in memory and overflows to disk if the data is larger than a predefined threashold.
    This prevents a large file from exhausting your hardware's memory.

## As bytes

Xpresso can read the entire file into memory if you'd like:

```python
--8<-- "docs_src/tutorial/file_as_bytes.py"
```

This can be convenient if you know the files are not large.

## Setting the content-type

You can set the media type via the `media_type` parameter to `File()` and enforce it via the `enforce_media_type` parameter:

```python
--8<-- "docs_src/tutorial/file_media_type.py"
```

Media types can be a media type (e.g. `image/png`) or a media type range (e.g. `image/*`).

If you do not explicitly set the media type, all media types are accepted.
Once you set an explicit media type, that media type in the requests' `Content-Type` header will be validated on incoming requests, but this behavior can be disabled via the `enforce_media_type` parameter to `File()`.

[multipart/form-data documentation]: forms.md#multipart-requests
