from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from app.models.database import Database


@dataclass
class ChecklistItem:
    id: str
    task_id: str
    title: str
    is_done: bool = False
    sort_order: int = 0


@dataclass
class Task:
    id: str
    title: str
    notes: str = ""
    status: str = "inbox"
    schedule: str = "inbox"
    due_date: Optional[str] = None
    scheduled_date: Optional[str] = None
    project_id: Optional[str] = None
    area_id: Optional[str] = None
    sort_order: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    tags: list = field(default_factory=list)
    checklist_items: list[ChecklistItem] = field(default_factory=list)


class TaskRepository:
    def __init__(self, db: Database):
        self.db = db

    def _row_to_task(self, row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            notes=row["notes"] or "",
            status=row["status"],
            schedule=row["schedule"],
            due_date=row["due_date"],
            scheduled_date=row["scheduled_date"],
            project_id=row["project_id"],
            area_id=row["area_id"],
            sort_order=row["sort_order"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
        )

    def _load_checklist(self, task: Task):
        rows = self.db.fetchall(
            "SELECT * FROM checklist_items WHERE task_id = ? ORDER BY sort_order",
            (task.id,),
        )
        task.checklist_items = [
            ChecklistItem(
                id=r["id"],
                task_id=r["task_id"],
                title=r["title"],
                is_done=bool(r["is_done"]),
                sort_order=r["sort_order"],
            )
            for r in rows
        ]

    def _load_tags(self, task: Task):
        rows = self.db.fetchall(
            """SELECT t.id, t.title, t.color FROM tags t
               JOIN task_tags tt ON t.id = tt.tag_id
               WHERE tt.task_id = ?""",
            (task.id,),
        )
        task.tags = [{"id": r["id"], "title": r["title"], "color": r["color"]} for r in rows]

    def create(self, title: str, **kwargs) -> Task:
        task_id = uuid4().hex
        schedule = kwargs.get("schedule", "inbox")
        status = "active" if schedule != "inbox" else "inbox"
        self.db.execute(
            """INSERT INTO tasks (id, title, notes, status, schedule, due_date,
               scheduled_date, project_id, area_id, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                title,
                kwargs.get("notes", ""),
                status,
                schedule,
                kwargs.get("due_date"),
                kwargs.get("scheduled_date"),
                kwargs.get("project_id"),
                kwargs.get("area_id"),
                kwargs.get("sort_order", 0),
            ),
        )
        return self.get_by_id(task_id)

    def update(self, task: Task) -> Task:
        self.db.execute(
            """UPDATE tasks SET title=?, notes=?, status=?, schedule=?, due_date=?,
               scheduled_date=?, project_id=?, area_id=?, sort_order=?,
               updated_at=datetime('now') WHERE id=?""",
            (
                task.title,
                task.notes,
                task.status,
                task.schedule,
                task.due_date,
                task.scheduled_date,
                task.project_id,
                task.area_id,
                task.sort_order,
                task.id,
            ),
        )
        return self.get_by_id(task.id)

    def delete(self, task_id: str):
        self.db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def get_by_id(self, task_id: str) -> Optional[Task]:
        row = self.db.fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not row:
            return None
        task = self._row_to_task(row)
        self._load_checklist(task)
        self._load_tags(task)
        return task

    def get_by_schedule(self, schedule: str) -> list[Task]:
        rows = self.db.fetchall(
            """SELECT * FROM tasks WHERE schedule = ? AND status != 'completed' AND status != 'cancelled'
               ORDER BY sort_order, created_at""",
            (schedule,),
        )
        return [self._row_to_task(r) for r in rows]

    def get_today(self) -> list[Task]:
        today = date.today().isoformat()
        rows = self.db.fetchall(
            """SELECT * FROM tasks
               WHERE (schedule = 'today' OR due_date = ?)
               AND status != 'completed' AND status != 'cancelled'
               ORDER BY sort_order, created_at""",
            (today,),
        )
        return [self._row_to_task(r) for r in rows]

    def get_upcoming(self) -> list[Task]:
        today = date.today().isoformat()
        rows = self.db.fetchall(
            """SELECT * FROM tasks
               WHERE (schedule = 'upcoming' OR (scheduled_date IS NOT NULL AND scheduled_date > ?))
               AND status != 'completed' AND status != 'cancelled'
               ORDER BY COALESCE(scheduled_date, '9999-12-31'), sort_order""",
            (today,),
        )
        return [self._row_to_task(r) for r in rows]

    def get_by_project(self, project_id: str) -> list[Task]:
        rows = self.db.fetchall(
            """SELECT * FROM tasks WHERE project_id = ? AND status != 'completed' AND status != 'cancelled'
               ORDER BY sort_order, created_at""",
            (project_id,),
        )
        return [self._row_to_task(r) for r in rows]

    def get_by_area(self, area_id: str) -> list[Task]:
        rows = self.db.fetchall(
            """SELECT * FROM tasks WHERE area_id = ? AND status != 'completed' AND status != 'cancelled'
               ORDER BY sort_order, created_at""",
            (area_id,),
        )
        return [self._row_to_task(r) for r in rows]

    def get_completed(self) -> list[Task]:
        rows = self.db.fetchall(
            "SELECT * FROM tasks WHERE status = 'completed' ORDER BY completed_at DESC"
        )
        return [self._row_to_task(r) for r in rows]

    def complete(self, task_id: str):
        self.db.execute(
            "UPDATE tasks SET status='completed', completed_at=datetime('now'), updated_at=datetime('now') WHERE id=?",
            (task_id,),
        )

    def uncomplete(self, task_id: str):
        self.db.execute(
            "UPDATE tasks SET status='active', completed_at=NULL, updated_at=datetime('now') WHERE id=?",
            (task_id,),
        )

    def move_to_schedule(self, task_id: str, schedule: str):
        status = "active" if schedule != "inbox" else "inbox"
        self.db.execute(
            "UPDATE tasks SET schedule=?, status=?, updated_at=datetime('now') WHERE id=?",
            (schedule, status, task_id),
        )

    def search(self, query: str) -> list[Task]:
        rows = self.db.fetchall(
            """SELECT tasks.* FROM tasks
               JOIN tasks_fts ON tasks.rowid = tasks_fts.rowid
               WHERE tasks_fts MATCH ?
               ORDER BY rank""",
            (query,),
        )
        return [self._row_to_task(r) for r in rows]

    def get_count_by_schedule(self, schedule: str) -> int:
        if schedule == "today":
            today = date.today().isoformat()
            row = self.db.fetchone(
                """SELECT COUNT(*) as cnt FROM tasks
                   WHERE (schedule = 'today' OR due_date = ?)
                   AND status != 'completed' AND status != 'cancelled'""",
                (today,),
            )
        else:
            row = self.db.fetchone(
                """SELECT COUNT(*) as cnt FROM tasks
                   WHERE schedule = ? AND status != 'completed' AND status != 'cancelled'""",
                (schedule,),
            )
        return row["cnt"] if row else 0

    # Checklist operations
    def add_checklist_item(self, task_id: str, title: str) -> ChecklistItem:
        item_id = uuid4().hex
        self.db.execute(
            "INSERT INTO checklist_items (id, task_id, title, sort_order) VALUES (?, ?, ?, ?)",
            (item_id, task_id, title, 0),
        )
        return ChecklistItem(id=item_id, task_id=task_id, title=title)

    def update_checklist_item(self, item_id: str, title: str = None, is_done: bool = None):
        if title is not None:
            self.db.execute("UPDATE checklist_items SET title=? WHERE id=?", (title, item_id))
        if is_done is not None:
            self.db.execute("UPDATE checklist_items SET is_done=? WHERE id=?", (int(is_done), item_id))

    def delete_checklist_item(self, item_id: str):
        self.db.execute("DELETE FROM checklist_items WHERE id=?", (item_id,))

    # Tag operations
    def set_tags(self, task_id: str, tag_ids: list[str]):
        self.db.execute("DELETE FROM task_tags WHERE task_id=?", (task_id,))
        for tag_id in tag_ids:
            self.db.execute(
                "INSERT INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                (task_id, tag_id),
            )
