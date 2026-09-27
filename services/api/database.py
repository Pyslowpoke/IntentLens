"""Server-configured read-only connectors. No client-controlled host paths or URLs."""
import json
import os
import sqlite3
import time
from pathlib import Path
import pandas as pd
import sqlalchemy as sa
import sqlglot
from sqlglot import exp


def sources():
    remote=json.loads(os.getenv("DB_SOURCES_JSON","{}"))
    local=json.loads(os.getenv("SQLITE_FILES_JSON","{}"))
    return {**{k:{"kind":sa.engine.make_url(v).get_backend_name()} for k,v in remote.items()},**{k:{"kind":"sqlite"} for k in local}}


def check_sql(sql,dialect=None):
    try:
        statements=sqlglot.parse(sql,read=dialect)
    except sqlglot.errors.ParseError as e:
        raise ValueError("SQL parse error; check the selected database dialect / SQL 语法错误") from e
    if len(statements)!=1 or not isinstance(statements[0],(exp.Select,exp.Union,exp.Subquery)):
        raise ValueError("Only one read-only SELECT query is supported")
    forbidden=(exp.Insert,exp.Update,exp.Delete,exp.Create,exp.Drop,exp.Command,exp.Into)
    if any(isinstance(n,forbidden) for n in statements[0].walk()): raise ValueError("Write operations are forbidden")


def sqlite_connection(id):
    allowed=json.loads(os.getenv("SQLITE_FILES_JSON","{}"))
    if id not in allowed: raise ValueError("SQLite source must be explicitly configured by the operator")
    path=Path(allowed[id]).resolve(strict=True)
    c=sqlite3.connect(path.as_uri()+"?mode=ro",uri=True)
    c.execute("PRAGMA query_only=ON")
    # Deny extension/file access, ATTACH, PRAGMA and every mutation at SQLite VM level.
    permitted={sqlite3.SQLITE_SELECT,sqlite3.SQLITE_READ,sqlite3.SQLITE_FUNCTION,sqlite3.SQLITE_RECURSIVE}
    def authorize(action,a,b,db,trigger):
        if action==sqlite3.SQLITE_PRAGMA and a in ("table_info","table_xinfo"): return sqlite3.SQLITE_OK
        if action not in permitted: return sqlite3.SQLITE_DENY
        if action==sqlite3.SQLITE_FUNCTION and str(b).lower() in ("load_extension","writefile","readfile"): return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    c.set_authorizer(authorize)
    deadline=time.monotonic()+5
    c.set_progress_handler(lambda:int(time.monotonic()>deadline),1000)
    return c


def query(id,sql,limit=10000):
    limit=min(max(int(limit),1),10000)
    configs=sources()
    if id not in configs: raise ValueError("Unknown configured data source")
    check_sql(sql,{"postgresql":"postgres","mysql":"mysql","sqlite":"sqlite"}[configs[id]["kind"]])
    if configs[id]["kind"]=="sqlite":
        with sqlite_connection(id) as c:
            cur=c.execute(sql)
            rows=cur.fetchmany(limit+1)
            columns=[d[0] for d in cur.description]
    else:
        url=json.loads(os.getenv("DB_SOURCES_JSON","{}"))[id]
        engine=sa.create_engine(url,connect_args={"connect_timeout":5},pool_pre_ping=True)
        try:
            with engine.connect() as c:
                if engine.dialect.name=="postgresql":
                    c.exec_driver_sql("SET TRANSACTION READ ONLY")
                    c.exec_driver_sql("SET LOCAL statement_timeout = '5000ms'")
                    if c.exec_driver_sql("SELECT rolsuper OR rolcreaterole OR rolcreatedb FROM pg_roles WHERE rolname=current_user").scalar(): raise ValueError("Refusing privileged PostgreSQL account; configure a restricted reader")
                    if c.execute(sa.text("SELECT has_table_privilege(current_user, oid, 'INSERT,UPDATE,DELETE,TRUNCATE') FROM pg_class WHERE relkind='r' AND relnamespace IN (SELECT oid FROM pg_namespace WHERE nspname NOT LIKE 'pg_%' AND nspname <> 'information_schema')")).scalars().all().count(True): raise ValueError("Reader account has write privileges")
                elif engine.dialect.name=="mysql":
                    grants=[str(r[0]).upper() for r in c.exec_driver_sql("SHOW GRANTS")]
                    for grant in grants:
                        privileges=grant.split(" ON ")[0].replace("GRANT ","")
                        if any(p.strip() not in ("SELECT","USAGE","SHOW VIEW") for p in privileges.split(",")): raise ValueError("MySQL account must have SELECT/USAGE only")
                    c.exec_driver_sql("SET SESSION MAX_EXECUTION_TIME=5000")
                    c.commit()
                    c.exec_driver_sql("START TRANSACTION READ ONLY")
                else: raise ValueError("Only PostgreSQL, MySQL and allowlisted SQLite supported")
                result=c.execution_options(stream_results=True).execute(sa.text(sql))
                columns=list(result.keys()); rows=result.fetchmany(limit+1)
                c.rollback()
        finally: engine.dispose()
    if len(rows)>limit: raise ValueError(f"Query exceeds {limit} rows; add aggregation or explicit LIMIT. No silent truncation.")
    df=pd.DataFrame(rows,columns=[f"f{i+1}" for i in range(len(columns))])
    return df,columns


def browse(id):
    kind=sources().get(id,{}).get("kind")
    sql={"sqlite":"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'","postgresql":"SELECT table_schema,table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position","mysql":"SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema=DATABASE() ORDER BY table_name,ordinal_position"}.get(kind)
    if not sql: raise ValueError("Unknown source")
    df,names=query(id,sql)
    if kind=="sqlite":
        entries=[]
        with sqlite_connection(id) as c:
            for table in df.iloc[:,0].tolist():
                for col in c.execute("SELECT name,type FROM pragma_table_info(?)",(table,)).fetchall():
                    entries.append({"table":table,"column":col[0],"type":col[1]})
        return {"columns":["table","column","type"],"rows":entries}
    return {"columns":names,"rows":df.to_dict("records")}
