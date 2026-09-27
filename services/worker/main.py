import json
from services.config import load_environment
load_environment("worker")
import logging
import os
import subprocess
import sys
import time
import hashlib
import shutil
from pathlib import Path
from services.api import store
from services.api.contracts import AnalysisPlan, ChartSpec, ChartRevision

log = logging.getLogger("worker")


def execute_job(id):
    import pandas as pd
    from services.api.compute import compute, cache_key
    from services.api.render import render, resolve
    with store.connect() as c:
        row=c.execute("SELECT * FROM jobs WHERE id=?",(id,)).fetchone()
    run,payload=json.loads(row["body"]),json.loads(row["payload"])
    dataset=store.get("dataset",run["dataset_id"])
    plan=AnalysisPlan.model_validate(payload["plan"])
    spec=ChartSpec.model_validate(payload["spec"])
    key=cache_key(dataset,plan)
    cached=store.root()/"cache"/f"{key}.json"
    start=time.perf_counter()
    hit=cached.exists()
    if hit: result=json.loads(cached.read_text(encoding="utf-8"))
    else:
        result=compute(pd.read_parquet(store.root()/dataset["snapshot"]),plan,dataset)
        cached.write_text(json.dumps(result,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    compute_ms=(time.perf_counter()-start)*1000
    dest=store.root()/"artifacts"/id
    render_key=hashlib.sha256((key+spec.model_dump_json()+"themes-v3-render-v8").encode()).hexdigest()
    render_cache=store.root()/"cache"/render_key
    render_hit=(render_cache/"manifest.json").exists()
    if render_hit:
        shutil.copytree(render_cache,dest,dirs_exist_ok=True)
        artifacts=json.loads((dest/"manifest.json").read_text())
    else:
        artifacts=render(result,spec,dest)
        shutil.copytree(dest,render_cache,dirs_exist_ok=True)
        (render_cache/"manifest.json").write_text(json.dumps(artifacts))
    code="from services.api.compute import compute\nfrom services.api.contracts import AnalysisPlan\nimport pandas as pd, json\n# Restore the referenced snapshot as data.parquet before running.\ndataset=json.load(open('dataset.json', encoding='utf-8'))\nplan=AnalysisPlan.model_validate(json.load(open('plan.json', encoding='utf-8')))\nresult=compute(pd.read_parquet('data.parquet'),plan,dataset)\nprint(result)\nfrom services.api.render import render\nfrom services.api.contracts import ChartSpec\nfrom pathlib import Path\nspec=ChartSpec.model_validate(json.load(open('chart.json', encoding='utf-8')))\nrender(result,spec,Path('output'))\n"
    revision=ChartRevision(id=id, chart_id=run["chart_id"],parent_id=run["parent_id"],dataset_id=run["dataset_id"],plan=plan,spec=spec,code=code,result=result,summary=payload["summary"],artifacts=artifacts,created_at=store.now()).model_dump()
    revision["result"]["execution"]={"compute_ms":compute_ms,"render_ms":(time.perf_counter()-start)*1000-compute_ms,"compute_cache_hit":hit,"render_cache_hit":render_hit,"engine":resolve(spec),"render_key":render_key}
    (dest/"revision.json").write_text(json.dumps(revision,ensure_ascii=False,allow_nan=False),encoding="utf-8")


def recover():
    with store.connect() as c:
        for row in c.execute("SELECT body FROM jobs WHERE status='running'").fetchall():
            store.event(c,json.loads(row[0]),"worker restarted; retry available / worker 重启，可重试","failed","Worker restarted")


def step():
    with store.connect() as c:
        c.execute("BEGIN IMMEDIATE")
        row=c.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY updated_at LIMIT 1").fetchone()
        if not row: return False
        run=json.loads(row["body"])
        store.event(c,run,"compute and render / 计算与绘图","running")
    # Explicit environment allowlist: child does not inherit model/database credentials.
    env={k:v for k,v in os.environ.items() if k.upper() in ("PATH","SYSTEMROOT","WINDIR","TEMP","TMP","HOME","USERPROFILE","LOCALAPPDATA","APPDATA","PLAYWRIGHT_BROWSERS_PATH","BROWSER_PATH","MPLCONFIGDIR","FONTCONFIG_PATH")}
    env.update(WORKBENCH_DATA=str(store.root()),PYTHONPATH=str(Path(__file__).resolve().parents[2]),PYTHONIOENCODING="utf-8")
    # A pipe can fill with font warnings while the parent waits for exit.
    # File-backed stderr prevents deadlock; only its tail is exposed on failure.
    import tempfile
    diagnostic=tempfile.TemporaryFile()
    p=subprocess.Popen([sys.executable,"-m","services.worker.main","--job",run["id"]],env=env,stdout=subprocess.DEVNULL,stderr=diagnostic)
    start=time.monotonic()
    timeout=float(os.getenv("RUN_TIMEOUT","120"))
    error=None
    while p.poll() is None:
        time.sleep(.2)
        with store.connect() as c:
            status=c.execute("SELECT status FROM jobs WHERE id=?",(run["id"],)).fetchone()[0]
        import psutil
        exceeded_memory=False
        try:
            tree=psutil.Process(p.pid)
            rss=tree.memory_info().rss+sum(child.memory_info().rss for child in tree.children(recursive=True) if child.is_running())
            exceeded_memory=rss > int(os.getenv("RUN_MAX_MB","3072"))*1024*1024
        except (psutil.NoSuchProcess,psutil.AccessDenied): pass
        if status != "running" or time.monotonic()-start>timeout or exceeded_memory:
            try:
                parent=psutil.Process(p.pid)
                for child in parent.children(recursive=True):
                    try: child.kill()
                    except psutil.NoSuchProcess: pass
                parent.kill()
            except psutil.NoSuchProcess: pass
            error=("Memory limit exceeded / 内存超限，请先聚合" if exceeded_memory else "Timeout; simplify the analysis or retry / 超时，可简化分析后重试") if status=="running" else "Cancelled or superseded"
            break
    p.wait()
    diagnostic.seek(0,2)
    diagnostic.seek(max(0,diagnostic.tell()-1600))
    stderr=diagnostic.read()
    diagnostic.close()
    with store.connect() as c:
        c.execute("BEGIN IMMEDIATE")
        current=json.loads(c.execute("SELECT body FROM jobs WHERE id=?",(run["id"],)).fetchone()[0])
        if current["status"] != "running": return True
        if error or p.returncode:
            store.event(c,current,"failed","failed",error or stderr.decode("utf-8",errors="replace")[-1600:])
            return True
        dest=store.root()/"artifacts"/run["id"]/"revision.json"
        revision=json.loads(dest.read_text(encoding="utf-8"))
        updated=c.execute("UPDATE projects SET head=?,updated_at=? WHERE id=? AND dataset_id=? AND generation=? AND head IS ?",(run["id"],store.now(),run["project_id"],run["dataset_id"],run["generation"],run["parent_id"]))
        if updated.rowcount:
            store.put("revision",revision,c)
            current["artifacts"]=revision["artifacts"]
            store.event(c,current,"complete","completed")
        else: store.event(c,current,"dataset or revision changed","stale")
    return True


def main():
    logging.basicConfig(level=logging.INFO)
    # Keep this handle alive for the lifetime of the worker.
    lock=(store.root()/"worker.lock").open("a+b")
    lock.seek(0);lock.write(b"0");lock.flush();lock.seek(0)
    try:
        if os.name=="nt":
            import msvcrt
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError:
        raise SystemExit("Another worker owns this data directory / 当前数据目录已有 worker")
    # Strip secrets even in local development.
    for key in list(os.environ):
        if any(s in key.upper() for s in ("API_KEY","DB_SOURCES","DATABASE_URL","MODEL_BASE","SQLITE_FILES")):
            os.environ.pop(key,None)
    recover()
    log.info("Single worker ready")
    while True:
        try:
            if not step(): time.sleep(.5)
        except Exception: log.exception("Worker loop error"); time.sleep(1)


if __name__=="__main__":
    if "--job" in sys.argv: execute_job(sys.argv[-1])
    else: main()
