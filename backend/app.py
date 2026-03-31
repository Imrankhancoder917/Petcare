"""
PetCare Connect Pro — Flask Backend Entry Point
"""
import os
from datetime import timedelta
from flask import Flask, send_from_directory, jsonify
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO, emit
from flask_cors import CORS

from config import Config
from models.db import init_db
from routes.auth import auth_bp
from routes.reports import reports_bp
from routes.assignments import assignments_bp
from routes.analytics import analytics_bp

app = Flask(__name__)
app.config.from_object(Config)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)

CORS(app, resources={r"/*": {"origins": "*"}})
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(assignments_bp)
app.register_blueprint(analytics_bp)


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


# SocketIO events
@socketio.on("connect")
def on_connect():
    emit("connected", {"message": "connected to PetCare Connect Pro"})


@socketio.on("new_report")
def broadcast_new_report(data):
    """Broadcast new report to all connected volunteers."""
    emit("report_notification", data, broadcast=True)


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "not found"}), 404


@app.errorhandler(413)
def request_too_large(e):
    return jsonify({"error": "file too large (max 16 MB)"}), 413


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "internal server error"}), 500


if __name__ == "__main__":
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as exc:
        print(f"Warning: could not initialize database: {exc}")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
