import json
import os
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone


def uid():
    return uuid.uuid4().hex


def now():
    return datetime.now(timezone.utc).isoformat()


def root():
    p = Path(os.environ.get("WORKBENCH_DATA", "data")).resolve()
    p.mkdir(parents=True, exist_ok=True)
    for folder in ("snapshots", "raw", "artifacts", "cache", "uploads"):
        (p / folder).mkdir(exist_ok=True)
    return p


def connect():
    c = sqlite3.connect(root() / "workbench.sqlite", timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS objects (kind TEXT, id TEXT, body TEXT NOT NULL, PRIMARY KEY(kind,id));
    CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, name TEXT, dataset_id TEXT, generation INTEGER DEFAULT 0, head TEXT, chart_id TEXT, updated_at TEXT);
    CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, status TEXT, body TEXT NOT NULL, payload TEXT NOT NULL, updated_at TEXT);
    CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, body TEXT);
    """)
    return c


def put(kind, obj, c=None):
    own = c is None
    c = c or connect()
    c.execute("INSERT OR REPLACE INTO objects VALUES(?,?,?)", (kind, obj["id"], json.dumps(obj, ensure_ascii=False, allow_nan=False)))
    if own:
        c.commit()
        c.close()


def get(kind, id):
    with connect() as c:
        r = c.execute("SELECT body FROM objects WHERE kind=? AND id=?", (kind, id)).fetchone()
    if not r:
        raise ValueError(f"Not found: {kind}/{id}")
    return json.loads(r["body"])


def project(id):
    with connect() as c:
        r = c.execute("SELECT * FROM projects WHERE id=?", (id,)).fetchone()
    if not r:
        raise ValueError("Project not found")
    return dict(r)


def event(c, run, stage, status=None, error=None):
    run.update(stage=stage, updated_at=now())
    if status:
        run["status"] = status
    run["error"] = error
    cur = c.execute("INSERT INTO events(run_id,body) VALUES(?,?)", (run["id"], json.dumps(run)))
    run["event_seq"] = cur.lastrowid
    c.execute("UPDATE events SET body=? WHERE seq=?", (json.dumps(run), cur.lastrowid))
    c.execute("UPDATE jobs SET status=?,body=?,updated_at=? WHERE id=?", (run["status"], json.dumps(run), now(), run["id"]))


def enqueue(project_id, plan, spec, summary, expected_head=None):
    from .contracts import Run
    with connect() as c:
        c.execute("BEGIN IMMEDIATE")
        p = dict(c.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone())
        if not p["dataset_id"]:
            raise ValueError("Import a dataset first")
        if expected_head != p["head"]:
            raise ValueError("Chart changed. Refresh the current revision / 图表版本已变化")
        r = Run(id=uid(), project_id=project_id, chart_id=p["chart_id"], dataset_id=p["dataset_id"], generation=p["generation"], parent_id=p["head"], created_at=now(), updated_at=now()).model_dump()
        payload = dict(plan=plan, spec=spec, summary=summary)
        # A newer request supersedes queued/running work for the same chart.
        for old in c.execute("SELECT body FROM jobs WHERE status IN ('queued','running')").fetchall():
            old = json.loads(old[0])
            if old["chart_id"] == p["chart_id"]:
                event(c, old, "superseded", "stale")
        c.execute("INSERT INTO jobs VALUES(?,?,?,?,?)", (r["id"], "queued", json.dumps(r), json.dumps(payload), now()))
        event(c, r, "queued")
    return r
