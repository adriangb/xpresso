import sqlite3
from dataclasses import dataclass
from typing import List

from xpresso import App, FromJson, Path


class SupportsWordsRepo:
    def add_word(self, word: str) -> None:
        raise NotImplementedError


@dataclass
class SQLiteWordsRepo(SupportsWordsRepo):
    conn: sqlite3.Connection

    def add_word(self, word: str) -> None:
        with self.conn:
            self.conn.execute("SELECT ?", (word,))


def add_word(repo: SupportsWordsRepo, word: FromJson[str]) -> str:
    repo.add_word(word)
    return word


routes = [Path("/words/", post=add_word)]


def create_app() -> App:
    conn = sqlite3.connect(":memory:")
    repo = SQLiteWordsRepo(conn)
    app = App(routes)
    app.dependency_overrides[SupportsWordsRepo] = lambda: repo
    return app


def test_add_word_endpoint() -> None:
    # this demonstrates how easy it is to swap
    # out an implementation with this pattern
    words: List[str] = []

    class TestWordsRepo(SupportsWordsRepo):
        def add_word(self, word: str) -> None:
            words.append(word)

    add_word(TestWordsRepo(), "hello")

    assert words == ["hello"]
