import pytest
from di import BaseContainer

from xpresso import App


def test_user_provided_container_with_incorrect_scopes() -> None:
    container = BaseContainer(scopes=("foo", "bar"))
    with pytest.raises(ValueError):
        App(container=container)
