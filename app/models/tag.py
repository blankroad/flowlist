from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from app.models.database import Database


@dataclass
class Tag:
    id: str
    title: str
    color: str = "#888888"


class TagRepository:
    def __init__(self, db: Database):
        self.db = db

    def create(self, title: str, color: str = "#888888") -> Tag:
        tag_id = uuid4().hex
        self.db.execute(
            "INSERT INTO tags (id, title, color) VALUES (?, ?, ?)",
            (tag_id, title, color),
        )
        return Tag(id=tag_id, title=title, color=color)

    def get_all(self) -> list[Tag]:
        rows = self.db.fetchall("SELECT * FROM tags ORDER BY title")
        return [Tag(id=r["id"], title=r["title"], color=r["color"]) for r in rows]

    def delete(self, tag_id: str):
        self.db.execute("DELETE FROM tags WHERE id = ?", (tag_id,))

    def update(self, tag: Tag):
        self.db.execute(
            "UPDATE tags SET title=?, color=? WHERE id=?",
            (tag.title, tag.color, tag.id),
        )
