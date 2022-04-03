# Files

You can read the request body directly into a file or bytes.
This will read the data from the top level request body, and can only support 1 file.
To receive multiple files, see the [multipart/form-data documentation].

```python
--8<-- "docs_src/tutorial/files/tutorial_001.py"
```

!!! note "Note"
    `UploadFile` is a class provided by Starlette that buffers the data in memory and overflows to disk if the data is larger than a predefined threshold.
    This prevents a large file from exhausting your hardware's memory, but does use disk space and CPU cycles for buffering.

!!! note "Implementation detail"
    `xpresso.UploadFile` is just a thin wrapper around `starlette.datastructures.UploadFile`, but you must use `xpresso.UploadFile` instead of `starlette.datastructures.UploadFile` directly, otherwise Xpresso won't know how to build the argument.

## As bytes

Xpresso can read the entire file into memory if you'd like:

```python
--8<-- "docs_src/tutorial/files/tutorial_002.py"
```

This can be convenient if you know the files are not large.

## As a stream

If you want to read the bytes without buffering to disk or memory, use `AsyncIterator[bytes]` as the type:

```python
--8<-- "docs_src/tutorial/files/tutorial_003.py"
```

## Setting the expected content-type

You can set the media type via the `media_type` parameter to `File()` and enforce it via the `enforce_media_type` parameter:

```python
--8<-- "docs_src/tutorial/files/tutorial_004.py"
```

Media types can be a media type (e.g. `image/png`) or a media type range (e.g. `image/*`).

If you do not explicitly set the media type, all media types are accepted.
Once you set an explicit media type, that media type in the requests' `Content-Type` header will be validated on incoming requests, but this behavior can be disabled via the `enforce_media_type` parameter to `File()`.

[multipart/form-data documentation]: forms.md#multipart-requests
