import json
import os

from flask import Flask, jsonify, render_template_string

from app_paths import LOCKDOWN_FILE, STATUS_FILE, atomic_write_json

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StackSentinel Dashboard</title>
    <style>
        :root { --green: #00ff41; --red: #ff3131; --bg: #0a0a0b; --card: #161b22; }
        body { background: var(--bg); color: var(--green); font-family: monospace; padding: 20px; }
        .card { background: var(--card); border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
        .box { padding: 10px 0; font-size: 16px; font-weight: bold; }
        .bar-bg { width: 100%; background: #333; border-radius: 4px; height: 20px; margin-top: 5px; overflow: hidden; }
        .bar-fill { height: 100%; background: var(--green); width: 0%; transition: width 0.5s ease-in-out, background 0.5s; }
        .log { background: #000; padding: 10px; color: #e6edf3; font-size: 13px; min-height: 80px; white-space: pre-wrap; border: 1px solid #333; }
        .btn-red { background: var(--red); color: white; width: 100%; padding: 15px; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; cursor: pointer; margin-bottom: 10px; text-transform: uppercase;}
        .btn-gray { background: #444; color: white; width: 100%; padding: 15px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
    </style>
</head>
<body>
    <h2 style="text-align:center;">🛡️ STACKSENTINEL</h2>

    <div class="card">
        <h3>System Vitals (<span id="status">ARMED</span>)</h3>
        <div class="box">
            CPU: <span id="cpu">0</span>%
            <div class="bar-bg"><div class="bar-fill" id="cpu-bar"></div></div>
        </div>
        <div class="box">
            RAM: <span id="ram">0</span>%
            <div class="bar-bg"><div class="bar-fill" id="ram-bar"></div></div>
        </div>
    </div>

    <div class="card" style="border-left: 4px solid var(--red);">
        <h3 style="color:var(--red); margin-top:0;">🧠 Latest AI Activity</h3>
        <div class="log" id="ai-log">Monitoring system logs...</div>
    </div>

    <button class="btn-red" onclick="triggerMode('lockdown')">🚨 INITIATE LOCKDOWN</button>
    <button class="btn-gray" onclick="triggerMode('unlock')">🔓 DISENGAGE LOCKDOWN</button>

    <script>
        setInterval(() => {
            fetch('/api/status?time=' + new Date().getTime()).then(r => r.json()).then(data => {
                let cpuVal = data.cpu || 0;
                let ramVal = data.ram || 0;

                document.getElementById('cpu').innerText = cpuVal;
                document.getElementById('ram').innerText = ramVal;

                let cpuBar = document.getElementById('cpu-bar');
                cpuBar.style.width = cpuVal + '%';
                cpuBar.style.background = cpuVal > 85 ? 'var(--red)' : 'var(--green)';

                let ramBar = document.getElementById('ram-bar');
                ramBar.style.width = ramVal + '%';
                ramBar.style.background = ramVal > 85 ? 'var(--red)' : 'var(--green)';

                let statEl = document.getElementById('status');
                statEl.innerText = data.status || 'OFFLINE';
                statEl.style.color = data.status === "🔒 LOCKDOWN" ? "var(--red)" : "var(--green)";

                if (data.last_log) document.getElementById('ai-log').innerText = data.last_log;
            });
        }, 1000);

        function triggerMode(action) {
            fetch('/api/' + action, { method: 'POST' }).then(r => r.json()).then(d => alert(d.message));
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/status")
def status():
    try:
        if STATUS_FILE.exists():
            with open(STATUS_FILE, "r", encoding="utf-8") as handle:
                return jsonify(json.load(handle))
        return jsonify({"cpu": 0, "ram": 0, "status": "WAITING"})
    except Exception:
        return jsonify({"cpu": 0, "ram": 0, "status": "FILE_LOCKED"})


@app.route("/api/lockdown", methods=["POST"])
def lockdown():
    try:
        atomic_write_json(LOCKDOWN_FILE, {"active": True}, mode=0o600)
        print("🚨 Dashboard: Lockdown file created.")
        return jsonify({"message": "Lockdown engaged. Watchdog taking over."})
    except Exception as exc:
        return jsonify({"message": f"Error: {exc}"})


@app.route("/api/unlock", methods=["POST"])
def unlock():
    try:
        if LOCKDOWN_FILE.exists():
            LOCKDOWN_FILE.unlink()
        print("🔓 Dashboard: Lockdown file removed.")
        return jsonify({"message": "System unlocked. Returning to armed state."})
    except Exception as exc:
        return jsonify({"message": f"Error: {exc}"})


def start_server():
    host = os.environ.get("STACKSENTINEL_UI_HOST", "127.0.0.1")
    port = int(os.environ.get("STACKSENTINEL_UI_PORT", "5000"))
    print(f"\n🌐 StackSentinel dashboard available at http://{host}:{port}\n")
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    start_server()
