from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from app.models.database import Database


@dataclass
class Area:
    id: str
    title: str
    sort_order: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AreaRepository:
    def __init__(self, db: Database):
        self.db = db

    def _row_to_area(self, row) -> Area:
        return Area(
            id=row["id"],
            title=row["title"],
            sort_order=row["sort_order"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create(self, title: str, **kwargs) -> Area:
        area_id = uuid4().hex
        self.db.execute(
            "INSERT INTO areas (id, title, sort_order) VALUES (?, ?, ?)",
            (area_id, title, kwargs.get("sort_order", 0)),
        )
        return self.get_by_id(area_id)

    def update(self, area: Area) -> Area:
        self.db.execute(
            "UPDATE areas SET title=?, sort_order=?, updated_at=datetime('now') WHERE id=?",
            (area.title, area.sort_order, area.id),
        )
        return self.get_by_id(area.id)

    def delete(self, area_id: str):
        self.db.execute("DELETE FROM areas WHERE id = ?", (area_id,))

    def get_by_id(self, area_id: str) -> Optional[Area]:
        row = self.db.fetchone("SELECT * FROM areas WHERE id = ?", (area_id,))
        if not row:
            return None
        return self._row_to_area(row)

    def get_all(self) -> list[Area]:
        rows = self.db.fetchall("SELECT * FROM areas ORDER BY sort_order, created_at")
        return [self._row_to_area(r) for r in rows]
