from flask import Flask, jsonify, request, render_template_string
import os
import json
from pyngrok import ngrok

app = Flask(__name__)

STATUS_FILE = "/tmp/stacksentinel_status.json"
LOCKDOWN_FILE = "/tmp/stacksentinel_lockdown.mode"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StackSentinel C2</title>
    <style>
        :root { --green: #00ff41; --red: #ff3131; --bg: #0a0a0b; --card: #161b22; }
        body { background: var(--bg); color: var(--green); font-family: monospace; padding: 20px; }
        .card { background: var(--card); border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
        .box { padding: 10px 0; font-size: 16px; font-weight: bold; }
        /* DYNAMIC PROGRESS BARS */
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
        <h3 style="color:var(--red); margin-top:0;">🧠 Amazon Nova AI Diagnosis</h3>
        <div class="log" id="ai-log">Monitoring system logs...</div>
    </div>

    <button class="btn-red" onclick="triggerMode('lockdown')">🚨 INITIATE LOCKDOWN</button>
    <button class="btn-gray" onclick="triggerMode('unlock')">🔓 DISENGAGE LOCKDOWN</button>

    <script>
        setInterval(() => {
            fetch('/api/status?time=' + new Date().getTime()).then(r => r.json()).then(data => {
                let cpuVal = data.cpu || 0;
                let ramVal = data.ram || 0;
                
                // Update text
                document.getElementById('cpu').innerText = cpuVal;
                document.getElementById('ram').innerText = ramVal;
                
                // Animate bars
                let cpuBar = document.getElementById('cpu-bar');
                cpuBar.style.width = cpuVal + '%';
                cpuBar.style.background = cpuVal > 85 ? 'var(--red)' : 'var(--green)';

                let ramBar = document.getElementById('ram-bar');
                ramBar.style.width = ramVal + '%';
                ramBar.style.background = ramVal > 85 ? 'var(--red)' : 'var(--green)';

                // Update Status & Logs
                let statEl = document.getElementById('status');
                statEl.innerText = data.status || 'OFFLINE';
                statEl.style.color = data.status === "🔒 LOCKDOWN" ? "var(--red)" : "var(--green)";
                
                if(data.last_log) document.getElementById('ai-log').innerText = data.last_log;
            });
        }, 1000);

        function triggerMode(action) {
            fetch('/api/' + action, { method: 'POST' }).then(r => r.json()).then(d => alert(d.message));
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def status():
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as f:
                return jsonify(json.load(f))
        return jsonify({"cpu": 0, "ram": 0, "status": "WAITING"})
    except:
        return jsonify({"cpu": 0, "ram": 0, "status": "FILE_LOCKED"})

@app.route('/api/lockdown', methods=['POST'])
def lockdown():
    """Drops the lockdown file for main.py to detect. NO SUBPROCESSES."""
    try:
        with open(LOCKDOWN_FILE, "w") as f:
            f.write("active")
        print("🚨 Remote C2: Lockdown file created.")
        return jsonify({"message": "Lockdown Engaged. Watchdog taking over."})
    except Exception as e:
        return jsonify({"message": f"Error: {e}"})

@app.route('/api/unlock', methods=['POST'])
def unlock():
    """Removes the lockdown file to return to normal watch mode."""
    try:
        if os.path.exists(LOCKDOWN_FILE):
            os.remove(LOCKDOWN_FILE)
        print("🔓 Remote C2: Lockdown file removed.")
        return jsonify({"message": "System Unlocked. Returning to Armed state."})
    except Exception as e:
        return jsonify({"message": f"Error: {e}"})

def start_server():
    # Start the Ngrok tunnel to the Flask port automatically
    public_url = ngrok.connect(5000)
    print(f"\n🌍 [SUCCESS] Public Dashboard Live At: {public_url.public_url}\n")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    start_server()