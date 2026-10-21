"""PiControl preview: deliberately contains no SSH or Wake-on-LAN executor."""
import argparse
import json
import secrets
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, abort, jsonify, render_template, request, session

ROOT = Path(__file__).resolve().parent
ACTIONS = {"on": "Encender", "off": "Apagar", "restart": "Reiniciar"}


def create_app(config_path=None, db_path=None):
    config = json.loads(Path(config_path or ROOT / "config.example.json").read_text(encoding="utf-8-sig"))
    if config.get("mode") != "simulation":
        raise ValueError("Esta versión solo admite mode=simulation. No ejecuta acciones reales.")
    zone = ZoneInfo(config["timezone"])
    database = Path(db_path or ROOT / "data" / "picontrol.sqlite3")
    database.parent.mkdir(parents=True, exist_ok=True)
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict", MAX_CONTENT_LENGTH=8192)
    servers = {s["id"]: s for s in config["servers"]}

    def db():
        conn = sqlite3.connect(database, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    conn = db()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS states(server TEXT PRIMARY KEY, state TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS schedules(
          id INTEGER PRIMARY KEY AUTOINCREMENT, server TEXT NOT NULL, action TEXT NOT NULL,
          days TEXT NOT NULL, time TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS runs(
          schedule_id INTEGER NOT NULL, local_minute TEXT NOT NULL,
          UNIQUE(schedule_id, local_minute));
        CREATE TABLE IF NOT EXISTS events(
          id INTEGER PRIMARY KEY, at TEXT NOT NULL, server TEXT NOT NULL,
          action TEXT NOT NULL, source TEXT NOT NULL, detail TEXT NOT NULL);
        """)
        for sid in servers:
            conn.execute("INSERT OR IGNORE INTO states VALUES (?, 'unknown')", (sid,))
    conn.close()

    @app.before_request
    def protect():
        # The preview has no login; only loopback hosts are allowed.
        if request.host.split(":")[0] not in {"127.0.0.1", "localhost"}:
            abort(403)
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            token = session.get("csrf", "")
            if not token or not secrets.compare_digest(token, request.headers.get("X-CSRF-Token", "")):
                abort(403)

    @app.after_request
    def headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        return response

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(409)
    def error(exc):
        return jsonify(error=str(exc.description)), exc.code

    def body():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            abort(400, "Se esperaba un objeto JSON.")
        return data

    def validate_target(data):
        sid, action = data.get("server"), data.get("action")
        if not isinstance(sid, str) or sid not in servers:
            abort(400, "Servidor desconocido.")
        if not isinstance(action, str) or action not in ACTIONS:
            abort(400, "Acción desconocida.")
        return sid, action

    def simulate(conn, sid, action, source, now):
        state = "off" if action == "off" else "on"
        conn.execute("UPDATE states SET state=? WHERE server=?", (state, sid))
        conn.execute("INSERT INTO events(at,server,action,source,detail) VALUES (?,?,?,?,?)",
                     (now.isoformat(), sid, action, source, "Simulación completada; no se contactó al equipo."))

    @app.get("/")
    def index():
        session.setdefault("csrf", secrets.token_hex(32))
        return render_template("index.html", csrf=session["csrf"])

    @app.get("/api/state")
    def state():
        conn = db()
        try:
            states = {r["server"]: r["state"] for r in conn.execute("SELECT * FROM states")}
            schedules = [dict(r) for r in conn.execute("SELECT * FROM schedules ORDER BY time,id")]
            for s in schedules:
                s["days"] = json.loads(s["days"])
                s["enabled"] = bool(s["enabled"])
            return jsonify(mode="simulation", timezone=config["timezone"], now=datetime.now(zone).isoformat(),
                           servers=[{"id": s["id"], "name": s["name"], "host": s["ssh_host"],
                                     "user": s["ssh_user"], "state": states[s["id"]]} for s in servers.values()],
                           schedules=schedules,
                           events=[dict(r) for r in conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100")])
        finally:
            conn.close()

    @app.post("/api/actions")
    def action():
        data = body()
        sid, selected = validate_target(data)
        if selected in {"off", "restart"} and data.get("confirmed") is not True:
            abort(400, "Confirma la acción antes de continuar.")
        conn = db()
        try:
            with conn:
                simulate(conn, sid, selected, "manual", datetime.now(zone))
        finally:
            conn.close()
        return jsonify(ok=True)

    @app.post("/api/schedules")
    def add_schedule():
        data = body()
        sid, selected = validate_target(data)
        days, clock = data.get("days"), data.get("time")
        if not isinstance(days, list) or not days or any(type(d) is not int or not 0 <= d <= 6 for d in days):
            abort(400, "Selecciona al menos un día válido.")
        if not isinstance(clock, str) or len(clock) != 5:
            abort(400, "Introduce una hora HH:MM.")
        try:
            parsed = datetime.strptime(clock, "%H:%M")
            if parsed.strftime("%H:%M") != clock:
                raise ValueError()
        except ValueError:
            abort(400, "La hora no es válida.")
        conn = db()
        try:
            with conn:
                conn.execute("INSERT INTO schedules(server,action,days,time) VALUES (?,?,?,?)",
                             (sid, selected, json.dumps(sorted(set(days))), clock))
        finally:
            conn.close()
        return jsonify(ok=True), 201

    @app.post("/api/schedules/<int:schedule_id>/toggle")
    def toggle(schedule_id):
        data = body()
        if type(data.get("enabled")) is not bool:
            abort(400, "Estado inválido.")
        conn = db()
        try:
            with conn:
                result = conn.execute("UPDATE schedules SET enabled=? WHERE id=?", (int(data["enabled"]), schedule_id))
                if not result.rowcount:
                    abort(404, "Horario no encontrado.")
        finally:
            conn.close()
        return jsonify(ok=True)

    @app.delete("/api/schedules/<int:schedule_id>")
    def delete(schedule_id):
        conn = db()
        try:
            with conn:
                if not conn.execute("DELETE FROM schedules WHERE id=?", (schedule_id,)).rowcount:
                    abort(404, "Horario no encontrado.")
        finally:
            conn.close()
        return jsonify(ok=True)

    def tick(now=None):
        now = now or datetime.now(zone)
        now = now.astimezone(zone)
        # Local date+minute deliberately excludes UTC offset: a repeated DST hour runs once.
        minute = now.strftime("%Y-%m-%d %H:%M")
        conn = db()
        try:
            with conn:
                conn.execute("BEGIN IMMEDIATE")
                for rule in conn.execute("SELECT * FROM schedules WHERE enabled=1 AND time=?", (now.strftime("%H:%M"),)).fetchall():
                    if now.weekday() not in json.loads(rule["days"]):
                        continue
                    claimed = conn.execute("INSERT OR IGNORE INTO runs VALUES (?,?)", (rule["id"], minute))
                    if claimed.rowcount:
                        simulate(conn, rule["server"], rule["action"], "horario", now)
        finally:
            conn.close()

    app.extensions["picontrol_tick"] = tick
    return app


if __name__ == "__main__":
    from waitress import serve
    parser = argparse.ArgumentParser(description="PiControl — panel local en simulación")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    app = create_app()
    stop = threading.Event()

    def scheduler():
        while not stop.is_set():
            try:
                app.extensions["picontrol_tick"]()
            except Exception:
                app.logger.exception("No se pudo procesar el horario")
            stop.wait(5)

    worker = threading.Thread(target=scheduler, daemon=True)
    worker.start()
    print(f"PiControl · SIMULACIÓN · http://127.0.0.1:{args.port}", flush=True)
    try:
        serve(app, host="127.0.0.1", port=args.port, threads=4)
    finally:
        stop.set()
        worker.join(timeout=10)
