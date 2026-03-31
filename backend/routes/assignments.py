from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.db import get_connection

assignments_bp = Blueprint("assignments", __name__)


@assignments_bp.route("/assign/<int:report_id>", methods=["POST"])
@jwt_required()
def assign_report(report_id):
    claims = get_jwt()
    role = claims.get("role", "user")
    volunteer_id = get_jwt_identity()

    if role not in ("volunteer", "admin"):
        return jsonify({"error": "only volunteers or admins can accept cases"}), 403

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Check report exists and is OPEN
            cur.execute("SELECT id, status FROM reports WHERE id = %s", (report_id,))
            report = cur.fetchone()
            if not report:
                return jsonify({"error": "report not found"}), 404
            if report["status"] not in ("OPEN",):
                return jsonify({"error": "report is not available for assignment"}), 409

            # Check not already assigned to someone else
            cur.execute(
                "SELECT id FROM assignments WHERE report_id = %s AND status = 'ACTIVE'",
                (report_id,),
            )
            if cur.fetchone():
                return jsonify({"error": "report already assigned to another volunteer"}), 409

            cur.execute(
                "INSERT INTO assignments (report_id, volunteer_id, status) VALUES (%s, %s, 'ACTIVE')",
                (report_id, volunteer_id),
            )
            cur.execute(
                "UPDATE reports SET status = 'ASSIGNED' WHERE id = %s", (report_id,)
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "case assigned successfully"}), 201


@assignments_bp.route("/assignments", methods=["GET"])
@jwt_required()
def get_assignments():
    claims = get_jwt()
    role = claims.get("role", "user")
    user_id = get_jwt_identity()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if role == "admin":
                cur.execute("""
                    SELECT a.id, a.report_id, a.volunteer_id, a.status, a.assigned_at,
                           r.title, r.urgency, r.status AS report_status,
                           u.name AS volunteer_name
                    FROM assignments a
                    JOIN reports r ON a.report_id = r.id
                    JOIN users u ON a.volunteer_id = u.id
                    ORDER BY a.assigned_at DESC
                """)
            else:
                cur.execute("""
                    SELECT a.id, a.report_id, a.volunteer_id, a.status, a.assigned_at,
                           r.title, r.urgency, r.status AS report_status,
                           u.name AS volunteer_name
                    FROM assignments a
                    JOIN reports r ON a.report_id = r.id
                    JOIN users u ON a.volunteer_id = u.id
                    WHERE a.volunteer_id = %s
                    ORDER BY a.assigned_at DESC
                """, (user_id,))
            rows = cur.fetchall()
    finally:
        conn.close()

    for row in rows:
        if row.get("assigned_at"):
            row["assigned_at"] = row["assigned_at"].isoformat()

    return jsonify(rows), 200
