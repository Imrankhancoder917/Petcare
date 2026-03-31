from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from models.db import get_connection

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics", methods=["GET"])
@jwt_required()
def get_analytics():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM reports")
            total = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) AS cnt FROM reports WHERE status = 'RESOLVED'")
            resolved = cur.fetchone()["cnt"]

            cur.execute("SELECT COUNT(*) AS cnt FROM reports WHERE urgency = 'HIGH'")
            high_urgency = cur.fetchone()["cnt"]

            cur.execute("SELECT COUNT(*) AS cnt FROM reports WHERE status = 'OPEN'")
            open_count = cur.fetchone()["cnt"]

            cur.execute("SELECT COUNT(*) AS cnt FROM reports WHERE status = 'ASSIGNED'")
            assigned_count = cur.fetchone()["cnt"]

            cur.execute("SELECT COUNT(*) AS cnt FROM reports WHERE status = 'IN_PROGRESS'")
            in_progress_count = cur.fetchone()["cnt"]

            # Reports per day (last 7 days)
            cur.execute("""
                SELECT DATE(created_at) AS day, COUNT(*) AS count
                FROM reports
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(created_at)
                ORDER BY day ASC
            """)
            daily_reports = cur.fetchall()

            # Status breakdown
            cur.execute("""
                SELECT status, COUNT(*) AS count FROM reports GROUP BY status
            """)
            status_breakdown = cur.fetchall()

    finally:
        conn.close()

    resolved_pct = round((resolved / total * 100), 1) if total else 0
    high_urgency_pct = round((high_urgency / total * 100), 1) if total else 0

    daily = [{"day": str(r["day"]), "count": r["count"]} for r in daily_reports]

    return jsonify({
        "total_reports": total,
        "resolved": resolved,
        "resolved_pct": resolved_pct,
        "high_urgency": high_urgency,
        "high_urgency_pct": high_urgency_pct,
        "open": open_count,
        "assigned": assigned_count,
        "in_progress": in_progress_count,
        "daily_reports": daily,
        "status_breakdown": [{"status": r["status"], "count": r["count"]} for r in status_breakdown],
    }), 200


@analytics_bp.route("/admin/users", methods=["GET"])
@jwt_required()
def list_users():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "admin only"}), 403

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email, role, created_at FROM users ORDER BY created_at DESC")
            users = cur.fetchall()
    finally:
        conn.close()

    for u in users:
        if u.get("created_at"):
            u["created_at"] = u["created_at"].isoformat()

    return jsonify(users), 200


@analytics_bp.route("/admin/users/<int:user_id>/role", methods=["PUT"])
@jwt_required()
def update_user_role(user_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "admin only"}), 403

    data = request.get_json(silent=True) or {}
    new_role = (data.get("role") or "").lower()
    if new_role not in ("user", "volunteer", "admin"):
        return jsonify({"error": "role must be user, volunteer, or admin"}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
            if cur.rowcount == 0:
                return jsonify({"error": "user not found"}), 404
        conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "role updated"}), 200
