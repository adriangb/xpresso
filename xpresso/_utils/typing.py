import sys

if sys.version_info < (3, 9):
    from typing_extensions import Annotated as Annotated  # noqa: F401
    from typing_extensions import get_args as get_args  # noqa: F401
    from typing_extensions import get_origin as get_origin  # noqa: F401
    from typing_extensions import get_type_hints as get_type_hints  # noqa: F401
else:
    from typing import Annotated as Annotated  # noqa: F401
    from typing import get_args as get_args  # noqa: F401
    from typing import get_origin as get_origin  # noqa: F401
    from typing import get_type_hints as get_type_hints  # noqa: F401

if sys.version_info < (3, 8):
    from typing_extensions import Literal as Literal  # noqa: F401
    from typing_extensions import Protocol as Protocol  # noqa: F401
else:

    from typing import Literal as Literal  # noqa: F401
    from typing import Protocol as Protocol  # noqa: F401
