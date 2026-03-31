import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
from PIL import Image
from models.db import get_connection
from ml.classifier import classify_urgency

reports_bp = Blueprint("reports", __name__)


def _allowed_file(filename: str) -> bool:
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def _is_valid_image(file_storage) -> bool:
    """Use Pillow to verify the uploaded file is a genuine image."""
    try:
        img = Image.open(file_storage)
        img.verify()  # raises on invalid images
        return True
    except Exception:
        return False
    finally:
        file_storage.seek(0)  # reset stream after verification


@reports_bp.route("/report", methods=["POST"])
@jwt_required()
def create_report():
    user_id = get_jwt_identity()
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    lat = request.form.get("lat")
    lng = request.form.get("lng")

    if not title or not description:
        return jsonify({"error": "title and description are required"}), 400

    # Parse coordinates
    try:
        lat = float(lat) if lat else None
        lng = float(lng) if lng else None
    except ValueError:
        return jsonify({"error": "lat and lng must be numbers"}), 400

    # Handle image upload
    image_filename = None
    if "image" in request.files:
        file = request.files["image"]
        if file and file.filename and _allowed_file(file.filename):
            if not _is_valid_image(file):
                return jsonify({"error": "uploaded file is not a valid image"}), 400
            ext = file.filename.rsplit(".", 1)[1].lower()
            image_filename = f"{uuid.uuid4().hex}.{ext}"
            upload_folder = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, image_filename))

    urgency = classify_urgency(description)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO reports (user_id, title, description, image, lat, lng, status, urgency)
                   VALUES (%s, %s, %s, %s, %s, %s, 'OPEN', %s)""",
                (user_id, title, description, image_filename, lat, lng, urgency),
            )
            report_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "report created", "id": report_id, "urgency": urgency}), 201


@reports_bp.route("/reports", methods=["GET"])
@jwt_required()
def get_reports():
    status_filter = request.args.get("status")
    urgency_filter = request.args.get("urgency")

    query = """
        SELECT r.id, r.title, r.description, r.image, r.lat, r.lng,
               r.status, r.urgency, r.created_at,
               u.name AS reporter_name, u.email AS reporter_email
        FROM reports r
        JOIN users u ON r.user_id = u.id
        WHERE 1=1
    """
    params = []
    if status_filter:
        query += " AND r.status = %s"
        params.append(status_filter.upper())
    if urgency_filter:
        query += " AND r.urgency = %s"
        params.append(urgency_filter.upper())
    query += " ORDER BY r.created_at DESC"

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
    finally:
        conn.close()

    for r in rows:
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
        if r.get("image"):
            r["image_url"] = f"/uploads/{r['image']}"
        else:
            r["image_url"] = None

    return jsonify(rows), 200


@reports_bp.route("/report/<int:report_id>", methods=["GET"])
@jwt_required()
def get_report(report_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT r.*, u.name AS reporter_name FROM reports r
                   JOIN users u ON r.user_id = u.id WHERE r.id = %s""",
                (report_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({"error": "report not found"}), 404

    if row.get("created_at"):
        row["created_at"] = row["created_at"].isoformat()
    if row.get("image"):
        row["image_url"] = f"/uploads/{row['image']}"
    else:
        row["image_url"] = None

    return jsonify(row), 200


@reports_bp.route("/update-status/<int:report_id>", methods=["PUT"])
@jwt_required()
def update_status(report_id):
    claims = get_jwt()
    role = claims.get("role", "user")
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").upper()

    valid_statuses = ("OPEN", "ASSIGNED", "IN_PROGRESS", "RESOLVED")
    if new_status not in valid_statuses:
        return jsonify({"error": f"status must be one of {valid_statuses}"}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, status FROM reports WHERE id = %s", (report_id,))
            report = cur.fetchone()
            if not report:
                return jsonify({"error": "report not found"}), 404

            # Volunteers can only update reports assigned to them
            if role == "volunteer":
                cur.execute(
                    "SELECT id FROM assignments WHERE report_id = %s AND volunteer_id = %s AND status = 'ACTIVE'",
                    (report_id, user_id),
                )
                if not cur.fetchone():
                    return jsonify({"error": "not authorized — not your assignment"}), 403

            cur.execute("UPDATE reports SET status = %s WHERE id = %s", (new_status, report_id))
            # If resolved, mark assignment completed
            if new_status == "RESOLVED":
                cur.execute(
                    "UPDATE assignments SET status = 'COMPLETED' WHERE report_id = %s AND status = 'ACTIVE'",
                    (report_id,),
                )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "status updated", "status": new_status}), 200
