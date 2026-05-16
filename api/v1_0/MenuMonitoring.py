# api/v1_0/MenuMonitoring.py

import json
from flask import Blueprint, jsonify, request, make_response
import pandas as pd
import config.connection as conn

from flask_jwt_extended import (
    get_jwt_identity,
    get_jwt
)

from api.v1_0.security import single_session_required

MenuMonitoring = Blueprint("MenuMonitoring", __name__)


# =========================================================
# GET ALL WITH FILTER & PAGINATION
# =========================================================
@MenuMonitoring.route("", methods=["GET"])
@single_session_required
def get_MenuMonitoring():

    conn_dsn = conn.dsn()

    current_user = get_jwt_identity()

    claims = get_jwt()
    role = claims.get("role", "user")

    # =========================
    # FILTER
    # =========================
    medsos_filter = request.args.get("medsos", "").strip()
    tgl_awal = request.args.get("tgl_awal")
    tgl_akhir = request.args.get("tgl_akhir")
    search_username = request.args.get("search_username")
    wilayah_filter = request.args.get("wilayah", "").strip()
    tema_filter = request.args.get("tema", "").strip()

    # =========================
    # PAGINATION
    # =========================
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    offset = (page - 1) * per_page

    print("🔍 FILTER:")
    print("medsos =", medsos_filter)
    print("tgl_awal =", tgl_awal)
    print("tgl_akhir =", tgl_akhir)
    print("search_username =", search_username)
    print("wilayah_filter =", wilayah_filter)
    print("tema_filter =", tema_filter)

    # =====================================================
    # BASE QUERY
    # =====================================================
    query = """
        SELECT
            mm.id,
            mm.medsos,
            mm.tema,

            TO_CHAR(mm.tgl_input, 'YYYY-MM-DD') AS tgl_input,

            u.kota AS wilayah,

            mm.user_input,
            mm.link,
            mm.username,
            REGEXP_REPLACE(mm.title, '[^[:ascii:]]', '', 'g') AS title,
            COALESCE(mm.view, '0') AS view,
            COALESCE(mm.liked, '0') AS liked,
            COALESCE(mm.comment, '0') AS comment,
            COALESCE(mm.share, '0') AS share,
            COALESCE(mm.saved, '0') AS saved,
            COALESCE(mm.engagement, '0') AS engagement,

            mm.video_id

        FROM dbo.monitoring_link mm
        LEFT JOIN dbo.user u
            ON u.userid = mm.user_input
    """

    # =====================================================
    # WHERE
    # =====================================================
    where_conditions = []
    params = []

    # =====================================================
    # ROLE FILTER
    # =====================================================
    if role == "02":

        where_conditions.append("""
            mm.user_input = ?
        """)

        params.append(current_user)

    elif role == "03":

        user_query = """
            SELECT kota
            FROM dbo.user
            WHERE userid = ?
        """

        user_df = pd.read_sql(
            user_query,
            conn_dsn,
            params=[current_user]
        )

        if not user_df.empty:

            user_kota = user_df.at[0, "kota"]

            where_conditions.append("""
                mm.user_input IN (
                    SELECT userid
                    FROM dbo.user
                    WHERE kota = ?
                )
            """)

            params.append(user_kota)

    # =====================================================
    # FILTER MEDSOS
    # =====================================================
    if medsos_filter and medsos_filter.upper() != "ALL":
        where_conditions.append("""
            UPPER(mm.medsos) = UPPER(?)
        """)

        params.append(medsos_filter)

    # =====================================================
    # FILTER TEMA
    # =====================================================
    if tema_filter and tema_filter.upper() != "ALL":
        where_conditions.append("""
            UPPER(mm.tema) = UPPER(?)
        """)

        params.append(tema_filter)

    # =====================================================
    # FILTER wilayah
    # =====================================================
    if wilayah_filter and wilayah_filter.upper() != "ALL":
        where_conditions.append("""
            UPPER(u.kota) = UPPER(?)
        """)

        params.append(wilayah_filter)

    # =====================================================
    # FILTER TANGGAL
    # =====================================================
    if tgl_awal:

        where_conditions.append("""
            mm.tgl_input >= ?
        """)

        params.append(tgl_awal)

    if tgl_akhir:

        where_conditions.append("""
            mm.tgl_input <= ?
        """)

        params.append(tgl_akhir)

    # =====================================================
    # SEARCH USERNAME
    # =====================================================
    if search_username:

        where_conditions.append("""
            (
                LOWER(mm.username) LIKE LOWER(?)
                OR LOWER(mm.user_input) LIKE LOWER(?)
            )
        """)

        search_param = f"%{search_username}%"

        params.append(search_param)
        params.append(search_param)

    # =====================================================
    # COMBINE WHERE
    # =====================================================
    where_clause = ""

    if where_conditions:
        where_clause = " WHERE " + " AND ".join(where_conditions)

    # =====================================================
    # COUNT QUERY
    # =====================================================
    count_query = """
        SELECT COUNT(*) AS total
        FROM dbo.monitoring_link mm
        LEFT JOIN dbo.user u
            ON u.userid = mm.user_input
    """

    count_query_full = count_query + where_clause

    count_df = pd.read_sql(
        count_query_full,
        conn_dsn,
        params=params
    )

    total_data = (
        int(count_df.at[0, "total"])
        if not count_df.empty else 0
    )

    total_pages = (
        (total_data + per_page - 1) // per_page
    )

    # =====================================================
    # FINAL QUERY
    # =====================================================
    query_full = query + where_clause

    query_full += """
         ORDER BY COALESCE(CAST(mm.engagement AS NUMERIC), 0) DESC,mm.tgl_input DESC,mm.medsos
    """

    query_full += f"""
        LIMIT {per_page}
        OFFSET {offset}
    """

    print("📡 QUERY:")
    print(query_full)

    print("📦 PARAMS:")
    print(params)

    try:

        df = pd.read_sql(
            query_full,
            conn_dsn,
            params=params
        )

        result = df.to_dict(orient="records")

        return jsonify({
            "logged_in_as": current_user,
            "role": role,
            "data": result,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_data": total_data,
                "total_pages": total_pages
            }
        }), 200

    except Exception as e:

        import traceback
        traceback.print_exc()

        return make_response(
            jsonify({
                "message": "Gagal ambil data monitoring",
                "error": str(e)
            }),
            500
        )


# =========================================================
# GET BY ID
# =========================================================
@MenuMonitoring.route("/<int:id>", methods=["GET"])
@single_session_required
def get_MenuMonitoring_by_id(id):

    conn_dsn = conn.dsn()

    query = """
        SELECT
            id,
            medsos,
            tema,

            TO_CHAR(tgl_input, 'YYYY-MM-DD') AS tgl_input,

            user_input,
            link,
            username,
            title,

            COALESCE(view, '0') AS view,
            COALESCE(liked, '0') AS liked,
            COALESCE(comment, '0') AS comment,
            COALESCE(share, '0') AS share,
            COALESCE(saved, '0') AS saved,
            COALESCE(engagement, '0') AS engagement,

            video_id

        FROM dbo.monitoring_link
        WHERE id = ?
    """

    try:

        df = pd.read_sql(
            query,
            conn_dsn,
            params=[id]
        )

        if df.empty:

            return jsonify({
                "message": "Data tidak ditemukan"
            }), 404

        return jsonify({
            "data": df.to_dict(orient="records")[0]
        }), 200

    except Exception as e:

        import traceback
        traceback.print_exc()

        return make_response(
            jsonify({
                "error": str(e)
            }),
            500
        )


# =========================================================
# DELETE
# =========================================================
@MenuMonitoring.route("/<int:id>", methods=["DELETE"])
@single_session_required
def delete_MenuMonitoring(id):

    conn_dsn = conn.dsn()

    current_user = get_jwt_identity()

    try:

        cursor = conn_dsn.cursor()

        cursor.execute("""
            DELETE FROM dbo.monitoring_link
            WHERE id = ?
        """, (id,))

        conn_dsn.commit()

        cursor.close()

        return jsonify({
            "logged_in_as": current_user,
            "message": "Data berhasil dihapus",
            "id": id
        }), 200

    except Exception as e:

        import traceback
        traceback.print_exc()

        return jsonify({
            "message": str(e)
        }), 500