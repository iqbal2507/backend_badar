from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt
)

from datetime import datetime
import pandas as pd
import traceback

import config.connection as conn

print("MENU DASHBOARD LOADED")

MenuDashboard = Blueprint("MenuDashboard", __name__)


# =====================================================
# HELPER
# =====================================================
def get_current_month_year():

    month = request.args.get("month")
    year = request.args.get("year")

    if not month:
        month = datetime.now().month

    if not year:
        year = datetime.now().year

    return int(month), int(year)



def get_user_kota(userid, conn_dsn):
    query = """
        SELECT kota
        FROM dbo.user
        WHERE userid = ?
    """

    df = pd.read_sql(query, conn_dsn, params=[userid])

    if df.empty:
        return None

    return df.at[0, "kota"]


# =====================================================
# THEME ENGAGEMENT (ROLE 00,01,02,03)
# =====================================================
@MenuDashboard.route("/theme-engagement", methods=["GET"])
@jwt_required()
def get_theme_engagement():

    conn_dsn = conn.dsn()

    claims = get_jwt()
    userid = get_jwt_identity()
    role = str(claims.get("role", "02")).zfill(2)

    month, year = get_current_month_year()
    wilayah = request.args.get("wilayah")

    try:

        # =========================
        # BASE QUERY
        # =========================
        query = """
            SELECT
                ml.tema,
                ROUND(COALESCE(AVG(CAST(ml.engagement AS NUMERIC)), 0), 2) AS engagement,
                COUNT(*) AS total_content
            FROM dbo.monitoring_link ml
            LEFT JOIN dbo.user u ON u.userid = ml.user_input
            WHERE EXTRACT(MONTH FROM ml.tgl_input) = ?
            AND EXTRACT(YEAR FROM ml.tgl_input) = ?
        """

        params = [month, year]

        # =========================
        # ROLE SECURITY
        # =========================
        if role not in ["00", "01"]:
            # role lain hanya data sendiri
            query += " AND ml.user_input = ? "
            params.append(userid)

        # =========================
        # WILAYAH FILTER (ADMIN ONLY)
        # =========================
        if wilayah and wilayah != "ALL":
            query += " AND UPPER(u.kota) = UPPER(?) "
            params.append(wilayah)

        # =========================
        # GROUPING
        # =========================
        query += """
            GROUP BY ml.tema
            ORDER BY engagement DESC
        """

        df = pd.read_sql(query, conn_dsn, params=params)

        return jsonify({
            "success": True,
            "role": role,
            "data": df.fillna(0).to_dict(orient="records")
        })

    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# =====================================================
# TASK PROGRESS ROLE 02
# =====================================================
@MenuDashboard.route("/task-progress", methods=["GET"])
@jwt_required()
def get_task_progress():
    print("masuk task-progress")

    conn_dsn = conn.dsn()

    claims = get_jwt()

    userid = get_jwt_identity()

    role = str(claims.get("role", "02")).zfill(2)

    month, year = get_current_month_year()

    try:

        query = """
            SELECT COUNT(*) AS total_tasks
            FROM dbo.inputan_link
            WHERE user_input = ?
            AND EXTRACT(MONTH FROM tgl_input) = ?
            AND EXTRACT(YEAR FROM tgl_input) = ?
        """


        params = [userid, month, year]

        print("========== TASK PROGRESS ==========")
        print(userid)
        print(query)
        print(params)

        df = pd.read_sql(
            query,
            conn_dsn,
            params=params
        )

        total_tasks = (
            int(df.at[0, "total_tasks"])
            if not df.empty else 0
        )

        required_tasks = 7

        percentage = 0

        if required_tasks > 0:
            percentage = (total_tasks / required_tasks) * 100

        return jsonify({
            "success": True,
            "role": role,
            "data": {
                "total_tasks": total_tasks,
                "required_tasks": required_tasks,
                "is_completed": total_tasks >= required_tasks,
                "percentage": round(percentage, 2)
            }
        })

    except Exception as e:

        traceback.print_exc()

        return make_response(
            jsonify({
                "success": False,
                "message": str(e)
            }),
            500
        )


# =====================================================
# USER CONTENT STATS ROLE 02
# =====================================================
@MenuDashboard.route("/user-content-stats", methods=["GET"])
@jwt_required()
def get_user_content_stats():
    print("masuk user-content-stats")

    conn_dsn = conn.dsn()

    claims = get_jwt()

    userid = get_jwt_identity()

    role = str(claims.get("role", "02")).zfill(2)

    month, year = get_current_month_year()

    try:

        query = """
            SELECT
                ml.username,

                COALESCE(SUM(CAST(ml.view AS BIGINT)),0) AS total_view,
                COALESCE(SUM(CAST(ml.liked AS BIGINT)),0) AS total_liked,
                COALESCE(SUM(CAST(ml.comment AS BIGINT)),0) AS total_comment,
                COALESCE(SUM(CAST(ml.share AS BIGINT)),0) AS total_share,
                COALESCE(SUM(CAST(ml.saved AS BIGINT)),0) AS total_saved,

                COALESCE(AVG(CAST(ml.engagement AS NUMERIC)),0) AS engagement

            FROM dbo.monitoring_link ml

            WHERE ml.user_input = ?
            AND EXTRACT(MONTH FROM ml.tgl_input) = ?
            AND EXTRACT(YEAR FROM ml.tgl_input) = ?

            GROUP BY ml.username
            ORDER BY engagement DESC
        """

        params = [userid, month, year]

        print("========== USER CONTENT ==========")
        print(query)
        print(params)

        df = pd.read_sql(
            query,
            conn_dsn,
            params=params
        )

        return jsonify({
            "success": True,
            "role": role,
            "data": df.to_dict(orient="records")
        })

    except Exception as e:

        traceback.print_exc()

        return make_response(
            jsonify({
                "success": False,
                "message": str(e)
            }),
            500
        )


# =====================================================
# TOP 10 USERNAME
# =====================================================
@MenuDashboard.route("/top-10-usernames", methods=["GET"])
@jwt_required()
def get_top_10_usernames():
    print("masuk top-10-username")

    conn_dsn = conn.dsn()

    claims = get_jwt()

    role = str(claims.get("role", "00")).zfill(2)

    month, year = get_current_month_year()

    wilayah = request.args.get("wilayah")

    try:

        query = """
            SELECT
                ml.username,
                u.kota as wilayah,
                COALESCE(AVG(CAST(ml.engagement AS NUMERIC)),0) AS engagement,

                COALESCE(SUM(CAST(ml.view AS BIGINT)),0) AS total_view,
                COALESCE(SUM(CAST(ml.liked AS BIGINT)),0) AS total_liked,
                COALESCE(SUM(CAST(ml.comment AS BIGINT)),0) AS total_comment,
                COALESCE(SUM(CAST(ml.share AS BIGINT)),0) AS total_share,
                COALESCE(SUM(CAST(ml.saved AS BIGINT)),0) AS total_saved

            FROM dbo.monitoring_link ml
            LEFT JOIN dbo.user u
                ON u.userid = ml.user_input

            WHERE EXTRACT(MONTH FROM ml.tgl_input) = ?
            AND EXTRACT(YEAR FROM ml.tgl_input) = ?
        """

        params = [month, year]

        if wilayah and wilayah.upper() != "ALL":

            query += """
                AND UPPER(u.kota) = UPPER(?)
            """

            params.append(wilayah)

        query += """
            GROUP BY ml.username,u.kota
            ORDER BY engagement DESC,u.kota
            LIMIT 10
        """

        print("========== TOP 10 ==========")
        print(query)
        print(params)

        df = pd.read_sql(
            query,
            conn_dsn,
            params=params
        )

        return jsonify({
            "success": True,
            "role": role,
            "data": df.to_dict(orient="records")
        })

    except Exception as e:

        traceback.print_exc()

        return make_response(
            jsonify({
                "success": False,
                "message": str(e)
            }),
            500
        )
@MenuDashboard.route("/overview", methods=["GET"])
@jwt_required()
def overview():
    conn_dsn = conn.dsn()

    claims = get_jwt()
    role = str(claims.get("role", "")).zfill(2)
    userid = get_jwt_identity()

    month, year = get_current_month_year()

    # default dari frontend
    wilayah = request.args.get("wilayah") or "ALL"

    # ambil kota user - PERBAIKAN DI SINI
    user_kota = get_user_kota(userid, conn_dsn)  # ✅ Gunakan userid, bukan claims

    # =========================
    # KOORDINATOR LOCK WILAYAH
    # =========================
    if role == "03" and user_kota:
        wilayah = user_kota

    query = """
    SELECT
        COUNT(ml.link) AS total_konten,
        COALESCE(SUM(CAST(ml.view AS BIGINT)),0) AS total_view,
        COALESCE(SUM(CAST(ml.liked AS BIGINT)),0) AS total_liked,
        COALESCE(SUM(CAST(ml.comment AS BIGINT)),0) AS total_comment,
        COALESCE(SUM(CAST(ml.share AS BIGINT)),0) AS total_share,
        COALESCE(SUM(CAST(ml.saved AS BIGINT)),0) AS total_saved,
        COALESCE(AVG(CAST(ml.engagement AS NUMERIC)),0) AS avg_engagement
    FROM dbo.monitoring_link ml
    LEFT JOIN dbo.user u ON u.userid = ml.user_input
    WHERE EXTRACT(MONTH FROM ml.tgl_input) = ?
    AND EXTRACT(YEAR FROM ml.tgl_input) = ?
    AND (
        ? = 'ALL'
        OR UPPER(u.kota) = UPPER(?)
    )
    """

    df = pd.read_sql(query, conn_dsn, params=[month, year, wilayah, wilayah])

    return jsonify({
        "success": True,
        "data": df.iloc[0].to_dict()
    })



# =====================================================
# CONTENT STATS BY WILAYAH
# =====================================================
@MenuDashboard.route("/content-stats-by-wilayah", methods=["GET"])
@jwt_required()
def get_content_stats_by_wilayah():
    print("masuk content-stats-by-wilayah")

    conn_dsn = conn.dsn()

    claims = get_jwt()
    userid = get_jwt_identity()  # ✅ Tambahkan
    role = str(claims.get("role", "03")).zfill(2)

    wilayah = request.args.get("wilayah")

    # ✅ LOCK WILAYAH UNTUK ROLE 03
    if role == "03":
        user_kota = get_user_kota(userid, conn_dsn)
        if user_kota:
            wilayah = user_kota
            print(f"🔒 Role 03 - Lock wilayah: {wilayah}")
        else:
            print(f"⚠️ Role 03 tapi kota tidak ditemukan untuk userid: {userid}")
            return jsonify({
                "success": False,
                "message": "Wilayah tidak ditemukan untuk user ini. Hubungi administrator."
            }), 400

    month, year = get_current_month_year()

    # ✅ Validasi wilayah wajib ada
    if not wilayah:
        return jsonify({
            "success": False,
            "message": "Parameter wilayah diperlukan"
        }), 400

    try:

        query = """
            SELECT
                u.kota AS wilayah,
                ml.username,
                COUNT(ml.link) AS total_konten, 
                COALESCE(SUM(CAST(ml.view AS BIGINT)),0) AS total_view,
                COALESCE(SUM(CAST(ml.liked AS BIGINT)),0) AS total_liked,
                COALESCE(SUM(CAST(ml.comment AS BIGINT)),0) AS total_comment,
                COALESCE(SUM(CAST(ml.share AS BIGINT)),0) AS total_share,
                COALESCE(SUM(CAST(ml.saved AS BIGINT)),0) AS total_saved,

                COALESCE(AVG(CAST(ml.engagement AS NUMERIC)),0) AS engagement

            FROM dbo.monitoring_link ml
            LEFT JOIN dbo.user u
                ON u.userid = ml.user_input

            WHERE UPPER(u.kota) = UPPER(?)
            AND EXTRACT(MONTH FROM ml.tgl_input) = ?
            AND EXTRACT(YEAR FROM ml.tgl_input) = ?

            GROUP BY u.kota, ml.username
            ORDER BY engagement DESC
        """

        params = [wilayah, month, year]

        print("========== BY WILAYAH ==========")
        print(f"Wilayah: {wilayah}")
        print(f"Params: {params}")

        df = pd.read_sql(
            query,
            conn_dsn,
            params=params
        )

        print(f"📊 Data ditemukan: {len(df)} rows")
        if len(df) > 0:
            print(f"Sample: {df.head(3).to_dict()}")

        return jsonify({
            "success": True,
            "role": role,
            "wilayah_used": wilayah,  # ✅ Return wilayah yang dipakai
            "data": df.to_dict(orient="records")
        })

    except Exception as e:

        traceback.print_exc()

        return make_response(
            jsonify({
                "success": False,
                "message": str(e)
            }),
            500
        )