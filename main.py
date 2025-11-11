import io
import os
import time
import uuid

import qrcode
from flask import Flask, request, jsonify, render_template, send_file, send_from_directory

app = Flask(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

os.makedirs(UPLOAD_DIR, exist_ok=True)

DEFAULT_FEATURES = {
    "timer": True,
    "message": True,
}

# ------------ State ------------

state = {"timers": {}}

# ------------ Helpers ------------

def get_remaining(timer):
    if not timer.get("running") or timer.get("end_ts") is None:
        return timer.get("duration", 0)
    remaining = int(timer["end_ts"] - time.time())
    return max(0, remaining)

def format_seconds(sec):
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def ensure_features(timer):
    if not isinstance(timer.get("features"), dict):
        timer["features"] = DEFAULT_FEATURES.copy()
    else:
        for key, default_value in DEFAULT_FEATURES.items():
            if key not in timer["features"]:
                timer["features"][key] = default_value
    return timer["features"]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def clear_timer_image(timer):
    filename = timer.get("image_filename")
    if not filename:
        timer["image_filename"] = None
        timer["image_url"] = None
        return
    path = os.path.join(UPLOAD_DIR, filename)
    try:
        os.remove(path)
    except OSError:
        pass
    timer["image_filename"] = None
    timer["image_url"] = None


# ------------ API Routes ------------

@app.route("/")
def control_root():
    return render_template("control.html")

@app.route("/display")
def display_page():
    return render_template("display.html")

@app.route("/api/state")
def api_state():
    timers_out = {}
    for tid, t in state["timers"].items():
        features = ensure_features(t).copy()
        timers_out[tid] = {
            "label": t["label"],
            "end_ts": t["end_ts"],
            "duration": t["duration"],
            "running": t["running"],
            "message": t["message"],
            "display_remaining": format_seconds(get_remaining(t)),
            "features": features,
            "image_url": t.get("image_url"),
        }
    return jsonify({"timers": timers_out})

@app.route("/api/timers/add", methods=["POST"])
def add_timer():
    if len(state["timers"]) < 3:
        new_id = str(max([int(k) for k in state["timers"].keys()] + [0]) + 1)
        state["timers"][new_id] = {
            "label": f"Event {new_id}",
            "end_ts": None,
            "duration": 0,
            "running": False,
            "message": "",
            "features": DEFAULT_FEATURES.copy(),
            "image_filename": None,
            "image_url": None,
        }
    return jsonify({"ok": True})

@app.route("/api/timer/<tid>/remove", methods=["POST"])
def remove_timer(tid):
    if tid in state["timers"]:
        clear_timer_image(state["timers"][tid])
        del state["timers"][tid]
    return jsonify({"ok": True})


@app.route("/api/timer/<tid>/label", methods=["POST"])
def api_timer_label(tid):
    data = request.get_json(force=True)
    label = data.get("label", "").strip()
    if tid in state["timers"]:
        state["timers"][tid]["label"] = label or state["timers"][tid]["label"]
    return jsonify({"ok": True})

@app.route("/api/timer/<tid>/start", methods=["POST"])
def api_timer_start(tid):
    data = request.get_json(force=True)
    duration = int(data.get("duration", 0))
    if duration < 0:
        duration = 0
    if tid in state["timers"]:
        now = time.time()
        state["timers"][tid]["duration"] = duration
        state["timers"][tid]["end_ts"] = now + duration
        state["timers"][tid]["running"] = True
    return jsonify({"ok": True})

@app.route("/api/timer/<tid>/stop", methods=["POST"])
def api_timer_stop(tid):
    if tid in state["timers"]:
        remaining = get_remaining(state["timers"][tid])
        state["timers"][tid]["duration"] = remaining
        state["timers"][tid]["end_ts"] = None
        state["timers"][tid]["running"] = False
    return jsonify({"ok": True})

@app.route("/api/timer/<tid>/reset", methods=["POST"])
def api_timer_reset(tid):
    if tid in state["timers"]:
        state["timers"][tid]["duration"] = 0
        state["timers"][tid]["end_ts"] = None
        state["timers"][tid]["running"] = False
    return jsonify({"ok": True})

@app.route("/api/timer/<tid>/message", methods=["POST"])
def api_message(tid):
    data = request.get_json(force=True)
    if tid in state["timers"]:
        state["timers"][tid]["message"] = data.get("message", "")[:256]
    return jsonify({"ok": True})

@app.route("/api/timer/<tid>/feature", methods=["POST"])
def api_timer_feature(tid):
    if tid not in state["timers"]:
        return jsonify({"error": "Timer not found"}), 404
    data = request.get_json(force=True)
    feature = data.get("feature")
    if feature not in DEFAULT_FEATURES:
        return jsonify({"error": "Unknown feature"}), 400
    enabled = bool(data.get("enabled"))
    timer = state["timers"][tid]
    features = ensure_features(timer)
    features[feature] = enabled
    if feature == "timer" and not enabled and timer.get("running"):
        remaining = get_remaining(timer)
        timer["duration"] = remaining
        timer["end_ts"] = None
        timer["running"] = False
    return jsonify({"ok": True, "features": features})


@app.route("/api/timer/<tid>/image", methods=["POST", "DELETE"])
def api_timer_image(tid):
    timer = state["timers"].get(tid)
    if not timer:
        return jsonify({"error": "Timer not found"}), 404

    if request.method == "DELETE":
        clear_timer_image(timer)
        return jsonify({"ok": True})

    if "image" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    upload = request.files["image"]
    original_name = (upload.filename or "").strip()
    if not upload or not original_name:
        return jsonify({"error": "Empty filename"}), 400

    if not allowed_file(original_name):
        return jsonify({"error": "Unsupported file type"}), 400

    ext = original_name.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    upload.save(path)

    clear_timer_image(timer)
    timer["image_filename"] = filename
    timer["image_url"] = f"/uploads/{filename}"
    return jsonify({"ok": True, "image_url": timer["image_url"]})


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/qr.png")
def qr_png():
    data = request.args.get("d", "").strip()
    if not data:
        return send_file(
            io.BytesIO(
                b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
                b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01"
                b"\x00\x00\x02\x02L\x01\x00;"
            ),
            mimetype="image/gif"
        )
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)