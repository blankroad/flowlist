from datetime import date, timedelta
from dataclasses import asdict

from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path

from app.config import DB_PATH
from app.models.database import Database
from app.models.task import TaskRepository, Task, ChecklistItem
from app.models.project import ProjectRepository
from app.models.area import AreaRepository
from app.models.tag import TagRepository

app = Flask(__name__, static_folder=str(Path(__file__).parent.parent / "static"))

db = Database(DB_PATH)
task_repo = TaskRepository(db)
project_repo = ProjectRepository(db)
area_repo = AreaRepository(db)
tag_repo = TagRepository(db)


# ── Helpers ──

def task_to_dict(t: Task) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "notes": t.notes,
        "status": t.status,
        "schedule": t.schedule,
        "due_date": t.due_date,
        "scheduled_date": t.scheduled_date,
        "project_id": t.project_id,
        "area_id": t.area_id,
        "sort_order": t.sort_order,
        "created_at": t.created_at,
        "updated_at": t.updated_at,
        "completed_at": t.completed_at,
        "tags": t.tags,
        "checklist_items": [
            {"id": c.id, "task_id": c.task_id, "title": c.title,
             "is_done": c.is_done, "sort_order": c.sort_order}
            for c in t.checklist_items
        ],
    }


def group_today(tasks):
    today_str = date.today().isoformat()
    overdue = [t for t in tasks if t.due_date and t.due_date < today_str]
    rest = [t for t in tasks if t not in overdue]
    groups = []
    if overdue:
        groups.append({"name": "Overdue", "tasks": [task_to_dict(t) for t in overdue]})
    if rest:
        groups.append({"name": "Today", "tasks": [task_to_dict(t) for t in rest]})
    return groups


def group_upcoming(tasks):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)
    buckets = {"Tomorrow": [], "This Week": [], "Next Week": [], "Later": []}
    for t in tasks:
        if t.scheduled_date:
            try:
                d = date.fromisoformat(t.scheduled_date)
            except ValueError:
                buckets["Later"].append(t)
                continue
            if d == tomorrow:
                buckets["Tomorrow"].append(t)
            elif d <= week_end:
                buckets["This Week"].append(t)
            elif d <= today + timedelta(days=14):
                buckets["Next Week"].append(t)
            else:
                buckets["Later"].append(t)
        else:
            buckets["This Week"].append(t)
    return [{"name": k, "tasks": [task_to_dict(t) for t in v]} for k, v in buckets.items() if v]


def group_logbook(tasks):
    today = date.today()
    yesterday = today - timedelta(days=1)
    buckets = {"Today": [], "Yesterday": [], "This Week": [], "Earlier": []}
    for t in tasks:
        if t.completed_at:
            try:
                d = date.fromisoformat(t.completed_at[:10])
            except ValueError:
                buckets["Earlier"].append(t)
                continue
            if d == today:
                buckets["Today"].append(t)
            elif d == yesterday:
                buckets["Yesterday"].append(t)
            elif d >= today - timedelta(days=7):
                buckets["This Week"].append(t)
            else:
                buckets["Earlier"].append(t)
        else:
            buckets["Earlier"].append(t)
    return [{"name": k, "tasks": [task_to_dict(t) for t in v]} for k, v in buckets.items() if v]


# ── Static files ──

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)


# ── Tasks API ──

@app.route("/api/tasks/view/<view_type>")
def get_tasks_by_view(view_type):
    entity_id = request.args.get("entity_id", "")

    if view_type == "inbox":
        tasks = task_repo.get_by_schedule("inbox")
        return jsonify({"title": "Inbox", "tasks": [task_to_dict(t) for t in tasks]})

    elif view_type == "today":
        tasks = task_repo.get_today()
        groups = group_today(tasks)
        return jsonify({"title": "Today", "tasks": [task_to_dict(t) for t in tasks], "groups": groups})

    elif view_type == "upcoming":
        tasks = task_repo.get_upcoming()
        groups = group_upcoming(tasks)
        return jsonify({"title": "Upcoming", "tasks": [task_to_dict(t) for t in tasks], "groups": groups})

    elif view_type == "anytime":
        tasks = task_repo.get_by_schedule("anytime")
        return jsonify({"title": "Anytime", "tasks": [task_to_dict(t) for t in tasks]})

    elif view_type == "someday":
        tasks = task_repo.get_by_schedule("someday")
        return jsonify({"title": "Someday", "tasks": [task_to_dict(t) for t in tasks]})

    elif view_type == "logbook":
        tasks = task_repo.get_completed()
        groups = group_logbook(tasks)
        return jsonify({"title": "Logbook", "tasks": [task_to_dict(t) for t in tasks], "groups": groups})

    elif view_type == "project":
        tasks = task_repo.get_by_project(entity_id)
        proj = project_repo.get_by_id(entity_id)
        title = proj.title if proj else "Project"
        return jsonify({"title": title, "tasks": [task_to_dict(t) for t in tasks]})

    elif view_type == "area":
        tasks = task_repo.get_by_area(entity_id)
        area = area_repo.get_by_id(entity_id)
        title = area.title if area else "Area"
        return jsonify({"title": title, "tasks": [task_to_dict(t) for t in tasks]})

    return jsonify({"title": view_type, "tasks": []})


@app.route("/api/tasks/<task_id>")
def get_task(task_id):
    task = task_repo.get_by_id(task_id)
    if not task:
        return jsonify({"error": "not found"}), 404
    return jsonify(task_to_dict(task))


@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.json
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400
    task = task_repo.create(title, **{k: v for k, v in data.items() if k != "title"})
    return jsonify(task_to_dict(task)), 201


@app.route("/api/tasks/<task_id>", methods=["PUT"])
def update_task(task_id):
    task = task_repo.get_by_id(task_id)
    if not task:
        return jsonify({"error": "not found"}), 404

    data = request.json
    if "title" in data:
        task.title = data["title"]
    if "notes" in data:
        task.notes = data["notes"]
    if "schedule" in data:
        task.schedule = data["schedule"]
        task.status = "active" if data["schedule"] != "inbox" else "inbox"
    if "due_date" in data:
        task.due_date = data["due_date"] or None
    if "scheduled_date" in data:
        task.scheduled_date = data["scheduled_date"] or None
    if "project_id" in data:
        task.project_id = data["project_id"] or None
    if "area_id" in data:
        task.area_id = data["area_id"] or None

    task = task_repo.update(task)
    return jsonify(task_to_dict(task))


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    task_repo.delete(task_id)
    return jsonify({"ok": True})


@app.route("/api/tasks/<task_id>/complete", methods=["POST"])
def complete_task(task_id):
    task_repo.complete(task_id)
    return jsonify({"ok": True})


@app.route("/api/tasks/<task_id>/uncomplete", methods=["POST"])
def uncomplete_task(task_id):
    task_repo.uncomplete(task_id)
    return jsonify({"ok": True})


# ── Checklist API ──

@app.route("/api/tasks/<task_id>/checklist", methods=["POST"])
def add_checklist_item(task_id):
    data = request.json
    title = data.get("title", "New item")
    item = task_repo.add_checklist_item(task_id, title)
    return jsonify({"id": item.id, "task_id": item.task_id, "title": item.title, "is_done": item.is_done}), 201


@app.route("/api/checklist/<item_id>", methods=["PUT"])
def update_checklist_item(item_id):
    data = request.json
    task_repo.update_checklist_item(
        item_id,
        title=data.get("title"),
        is_done=data.get("is_done"),
    )
    return jsonify({"ok": True})


@app.route("/api/checklist/<item_id>", methods=["DELETE"])
def delete_checklist_item(item_id):
    task_repo.delete_checklist_item(item_id)
    return jsonify({"ok": True})


# ── Search ──

@app.route("/api/search")
def search_tasks():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    try:
        tasks = task_repo.search(q)
    except Exception:
        tasks = []
    return jsonify([task_to_dict(t) for t in tasks[:20]])


# ── Sidebar data ──

@app.route("/api/sidebar")
def sidebar_data():
    counts = {}
    for s in ["inbox", "today", "upcoming", "anytime", "someday"]:
        counts[s] = task_repo.get_count_by_schedule(s)
    counts["logbook"] = len(task_repo.get_completed())

    projects = [
        {"id": p.id, "title": p.title, "task_count": p.task_count}
        for p in project_repo.get_all_active()
    ]
    areas = [
        {"id": a.id, "title": a.title}
        for a in area_repo.get_all()
    ]
    return jsonify({"counts": counts, "projects": projects, "areas": areas})


# ── Projects API ──

@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.json
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400
    proj = project_repo.create(title)
    return jsonify({"id": proj.id, "title": proj.title}), 201


@app.route("/api/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    project_repo.delete(project_id)
    return jsonify({"ok": True})


# ── Areas API ──

@app.route("/api/areas", methods=["POST"])
def create_area():
    data = request.json
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400
    area = area_repo.create(title)
    return jsonify({"id": area.id, "title": area.title}), 201


@app.route("/api/areas/<area_id>", methods=["DELETE"])
def delete_area(area_id):
    area_repo.delete(area_id)
    return jsonify({"ok": True})


# ── Tags API ──

@app.route("/api/tags")
def get_tags():
    tags = tag_repo.get_all()
    return jsonify([{"id": t.id, "title": t.title, "color": t.color} for t in tags])


@app.route("/api/tags", methods=["POST"])
def create_tag():
    data = request.json
    tag = tag_repo.create(data.get("title", ""), data.get("color", "#888888"))
    return jsonify({"id": tag.id, "title": tag.title, "color": tag.color}), 201
