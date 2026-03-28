from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from app.models.database import Database


@dataclass
class Project:
    id: str
    title: str
    notes: str = ""
    area_id: Optional[str] = None
    status: str = "active"
    deadline: Optional[str] = None
    sort_order: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    task_count: int = 0


class ProjectRepository:
    def __init__(self, db: Database):
        self.db = db

    def _row_to_project(self, row) -> Project:
        return Project(
            id=row["id"],
            title=row["title"],
            notes=row["notes"] or "",
            area_id=row["area_id"],
            status=row["status"],
            deadline=row["deadline"],
            sort_order=row["sort_order"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
        )

    def create(self, title: str, **kwargs) -> Project:
        project_id = uuid4().hex
        self.db.execute(
            """INSERT INTO projects (id, title, notes, area_id, deadline, sort_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                title,
                kwargs.get("notes", ""),
                kwargs.get("area_id"),
                kwargs.get("deadline"),
                kwargs.get("sort_order", 0),
            ),
        )
        return self.get_by_id(project_id)

    def update(self, project: Project) -> Project:
        self.db.execute(
            """UPDATE projects SET title=?, notes=?, area_id=?, status=?,
               deadline=?, sort_order=?, updated_at=datetime('now') WHERE id=?""",
            (project.title, project.notes, project.area_id, project.status,
             project.deadline, project.sort_order, project.id),
        )
        return self.get_by_id(project.id)

    def delete(self, project_id: str):
        self.db.execute("DELETE FROM projects WHERE id = ?", (project_id,))

    def get_by_id(self, project_id: str) -> Optional[Project]:
        row = self.db.fetchone("SELECT * FROM projects WHERE id = ?", (project_id,))
        if not row:
            return None
        return self._row_to_project(row)

    def get_all_active(self) -> list[Project]:
        rows = self.db.fetchall(
            """SELECT p.*, COUNT(t.id) as task_count
               FROM projects p
               LEFT JOIN tasks t ON t.project_id = p.id AND t.status != 'completed' AND t.status != 'cancelled'
               WHERE p.status = 'active'
               GROUP BY p.id
               ORDER BY p.sort_order, p.created_at""",
        )
        projects = []
        for r in rows:
            p = self._row_to_project(r)
            p.task_count = r["task_count"]
            projects.append(p)
        return projects

    def complete(self, project_id: str):
        self.db.execute(
            "UPDATE projects SET status='completed', completed_at=datetime('now') WHERE id=?",
            (project_id,),
        )
