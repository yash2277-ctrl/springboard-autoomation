"""
╔═══════════════════════════════════════════════════════════════════════╗
║       SPRINGBOARD AUTO — WEB SERVER (Flask + SSE Live Logs)         ║
║                                                                     ║
║  Provides a beautiful web UI for the Playwright automation.         ║
║  Users enter credentials → automation runs → live logs stream.      ║
║                                                                     ║
║  Usage:  python app.py                                              ║
║  Open:   http://localhost:5000                                      ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import json
import queue
import threading
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response

# ── Import the automation engine ─────────────────────────────────────
from springboard_engine import SpringboardAutomation

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ── Global state for active sessions ─────────────────────────────────
sessions = {}   # session_id -> { "status", "logs_queue", "thread", "engine" }


# ═══════════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Serve the main page."""
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def start_automation():
    """Start a new automation session."""
    data = request.json
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    course_url = data.get("course_url", "").strip()
    headless = data.get("headless", False)

    if not email or not password or not course_url:
        return jsonify({"error": "All fields are required."}), 400

    session_id = str(uuid.uuid4())[:8]
    log_queue = queue.Queue()

    engine = SpringboardAutomation(
        email=email,
        password=password,
        course_url=course_url,
        headless=headless,
        log_callback=lambda msg, level: log_queue.put({"msg": msg, "level": level, "time": datetime.now().strftime("%H:%M:%S")}),
    )

    sessions[session_id] = {
        "status": "running",
        "logs_queue": log_queue,
        "engine": engine,
        "thread": None,
    }

    def run_engine():
        try:
            engine.run()
            sessions[session_id]["status"] = "completed"
            log_queue.put({"msg": "Automation finished!", "level": "OK", "time": datetime.now().strftime("%H:%M:%S")})
        except Exception as e:
            sessions[session_id]["status"] = "error"
            log_queue.put({"msg": f"Fatal error: {e}", "level": "ERR", "time": datetime.now().strftime("%H:%M:%S")})
        finally:
            log_queue.put(None)  # Sentinel to close the SSE stream

    thread = threading.Thread(target=run_engine, daemon=True)
    sessions[session_id]["thread"] = thread
    thread.start()

    return jsonify({"session_id": session_id, "status": "started"})


@app.route("/api/logs/<session_id>")
def stream_logs(session_id):
    """SSE endpoint — streams live log messages to the frontend."""
    if session_id not in sessions:
        return jsonify({"error": "Session not found."}), 404

    def generate():
        q = sessions[session_id]["logs_queue"]
        while True:
            try:
                item = q.get(timeout=30)
                if item is None:
                    # Send final status
                    status = sessions[session_id]["status"]
                    yield f"data: {json.dumps({'type': 'done', 'status': status})}\n\n"
                    break
                yield f"data: {json.dumps({'type': 'log', **item})}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/stop/<session_id>", methods=["POST"])
def stop_automation(session_id):
    """Stop a running automation session."""
    if session_id not in sessions:
        return jsonify({"error": "Session not found."}), 404

    engine = sessions[session_id].get("engine")
    if engine:
        engine.stop()
    sessions[session_id]["status"] = "stopped"
    return jsonify({"status": "stopped"})


@app.route("/api/status/<session_id>")
def get_status(session_id):
    """Get current status of a session."""
    if session_id not in sessions:
        return jsonify({"error": "Session not found."}), 404
    return jsonify({"status": sessions[session_id]["status"]})


# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("  ╔═══════════════════════════════════════════════════╗")
    print("  ║   🚀  Springboard Auto — Web Server              ║")
    print("  ║   Open: http://localhost:5000                    ║")
    print("  ╚═══════════════════════════════════════════════════╝")
    print()
    app.run(debug=False, port=5000, threaded=True)
