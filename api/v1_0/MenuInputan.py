# api/v1_0/MenuInputan.py
import json
from datetime import datetime, date
from flask import Blueprint, jsonify, request, make_response
import pandas as pd
import config.connection as conn
from flask_jwt_extended import get_jwt_identity, get_jwt
from api.v1_0.security import single_session_required

MenuInputan = Blueprint('MenuInputan', __name__)


# ================= GET ALL WITH FILTER & PAGINATION =================
@MenuInputan.route("", methods=["GET"])
@single_session_required
def get_MenuInputan():
    conn_dsn = conn.dsn()
    current_user = get_jwt_identity()

    # Ambil role dari JWT claims
    claims = get_jwt()
    role = claims.get("role", "user")

    # Ambil parameter filter dari query string
    medsos_filter = request.args.get("medsos", "").strip()
    tgl_awal = request.args.get("tgl_awal")
    tgl_akhir = request.args.get("tgl_akhir")

    # Pagination parameters
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 30))
    offset = (page - 1) * per_page

    print(f"🔍 FILTER PARAMS: medsos={medsos_filter}, tgl_awal={tgl_awal}, tgl_akhir={tgl_akhir}")
    print(f"📄 PAGINATION: page={page}, per_page={per_page}, offset={offset}")

    # Base query
    query = """
        SELECT 
            il.id,
            il.medsos,
            il.tema,
            il.link,
            il.user_input,
             TO_CHAR(il.tgl_input, 'YYYY-MM-DD') as tgl_input,
            il.user_update,
            CASE 
                WHEN il.tgl_update IS NOT NULL 
            THEN TO_CHAR(il.tgl_update, 'YYYY-MM-DD') ELSE NULL 
            END as tgl_update
        FROM dbo.inputan_link il
    """

    # Count query (untuk total data)
    count_query = """
        SELECT COUNT(*) as total
        FROM dbo.inputan_link il
    """

    # Build WHERE conditions based on role
    where_conditions = []
    params = []

    # Role-based filtering
    if role == "02":  # Konten Kreator - hanya lihat data sendiri
        where_conditions.append("il.user_input = ?")
        params.append(current_user)
    elif role == "03":  # Koordinator Wilayah - lihat data se-kota
        # Ambil kota user yang login
        user_query = "SELECT kota FROM dbo.user WHERE userid = ?"
        user_df = pd.read_sql(user_query, conn_dsn, params=[current_user])

        if not user_df.empty:
            user_kota = user_df.at[0, "kota"]
            where_conditions.append("""
                il.user_input IN (
                    SELECT userid FROM dbo.user WHERE kota = ?
                )
            """)
            params.append(user_kota)
    # Role 00 (Super Admin) dan 01 (Admin) bisa lihat semua - no filter

    # Filter by medsos
    if medsos_filter and medsos_filter.upper() != "ALL":
        where_conditions.append("UPPER(il.medsos) = UPPER(?)")
        params.append(medsos_filter)
        print(f"✅ Adding medsos filter: {medsos_filter}")

    # Filter by date range
    if tgl_awal:
        where_conditions.append("il.tgl_input >= ?")
        params.append(tgl_awal)
        print(f"✅ Adding tgl_awal filter: {tgl_awal}")

    if tgl_akhir:
        where_conditions.append("il.tgl_input <= ?")
        params.append(tgl_akhir)
        print(f"✅ Adding tgl_akhir filter: {tgl_akhir}")

    # Combine WHERE conditions
    where_clause = ""
    if where_conditions:
        where_clause = " WHERE " + " AND ".join(where_conditions)

    # Get total count
    count_query_full = count_query + where_clause
    count_df = pd.read_sql(count_query_full, conn_dsn, params=params)
    total_data = int(count_df.at[0, "total"]) if not count_df.empty else 0
    total_pages = (total_data + per_page - 1) // per_page

    print(f"📊 Total data: {total_data}, Total pages: {total_pages}")

    # Build final query with pagination
    query_full = query + where_clause + " ORDER BY il.tgl_input DESC"

    # Add pagination
    query_full += f" LIMIT {per_page}  OFFSET   {offset} "

    try:
        df = pd.read_sql(query_full, conn_dsn, params=params)

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
        return make_response(jsonify({"error": str(e)}), 500)


# ================= GET BY ID =================
@MenuInputan.route("/<int:id>", methods=["GET"])
@single_session_required
def get_MenuInputan_by_id(id):
    conn_dsn = conn.dsn()

    query = """
        SELECT 
            id,
            medsos,
            tema,
            link,
            user_input,
            TO_CHAR(tgl_input, 'YYYY-MM-DD') as tgl_input,
            user_update,
            CASE 
                WHEN tgl_update IS NOT NULL 
                THEN TO_CHAR(tgl_update, 'YYYY-MM-DD')
                ELSE NULL
            END as tgl_update
        FROM dbo.inputan_link
        WHERE id = ?
    """

    try:
        df = pd.read_sql(query, conn_dsn, params=[id])

        if df.empty:
            return jsonify({
                "message": "Data tidak ditemukan"
            }), 404

        return jsonify(
            data=df.to_dict(orient="records")[0]
        ), 200

    except Exception as e:
        import traceback
        traceback.print_exc()

        return make_response(
            jsonify({"error": str(e)}),
            500
        )

# ================= CREATE =================
@MenuInputan.route("", methods=["POST"])
@single_session_required
def create_MenuInputan():
    try:
        print("🔥 CREATE INPUTAN START")

        conn_dsn = conn.dsn()
        current_user = get_jwt_identity()

        # Ambil dari JSON body
        data = request.get_json()

        medsos = data.get("medsos")
        tema = data.get("tema")
        link = data.get("link")

        # Validasi
        if not medsos or not link:
            return jsonify({"message": "medsos & link wajib diisi"}), 400


        # ================= CEK DUPLICATE LINK =================
        duplicate_query = """
            SELECT 
                il.link,
                il.user_input,
                il.tgl_input,
                u.kota
            FROM dbo.inputan_link il
            LEFT JOIN dbo.user u 
                ON u.userid = il.user_input
            WHERE LOWER(TRIM(il.link)) = LOWER(TRIM(?))
        """

        duplicate_df = pd.read_sql(
            duplicate_query,
            conn_dsn,
            params=[link]
        )

        if not duplicate_df.empty:
            user_input_db = duplicate_df.at[0, "user_input"] or "-"
            kota_db = duplicate_df.at[0, "kota"] or "-"
            tgl_input_db = duplicate_df.at[0, "tgl_input"] or "-"

            return jsonify({
                "message": f"Link tersebut sudah pernah diinput oleh user '{user_input_db}' di cabang '{kota_db}' pada tanggal '{tgl_input_db}'"
            }), 400


        # Auto-fill user_input & tgl_input
        user_input = current_user
        tgl_input = datetime.now().date()

        # INSERT
        query = """
            INSERT INTO dbo.inputan_link
            (medsos, tema, link, user_input, tgl_input)
            VALUES (?, ?, ?, ?, ?)
        """

        with conn_dsn.cursor() as cursor:
            cursor.execute(query, (
                medsos,
                tema,
                link,
                user_input,
                tgl_input
            ))
            conn_dsn.commit()

        print("✅ INPUTAN CREATED SUCCESS")

        return jsonify({
            "message": "Data berhasil ditambahkan"
        }), 201

    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500

# ================= UPDATE =================
@MenuInputan.route("/<int:id>", methods=["PUT"])
@single_session_required
def update_MenuInputan(id):
    try:

        print(f"🔥 UPDATE INPUTAN ID={id} START")

        conn_dsn = conn.dsn()
        current_user = get_jwt_identity()

        # Ambil dari JSON body
        data = request.get_json()

        medsos = data.get("medsos")
        tema = data.get("tema")
        link = data.get("link")

        # Validasi
        if not medsos or not link:
            return jsonify({"message": "medsos & link wajib diisi"}), 400

        # ================= CEK DUPLICATE LINK =================
        duplicate_query = """
            SELECT 
                il.link,
                il.user_input,
                il.tgl_input,
                u.kota
            FROM dbo.inputan_link il
            LEFT JOIN dbo.user u 
                ON u.userid = il.user_input
            WHERE LOWER(TRIM(il.link)) = LOWER(TRIM(?))
            AND il.id <> ?
          
        """

        duplicate_df = pd.read_sql(
            duplicate_query,
            conn_dsn,
            params=[link,id]
        )

        if not duplicate_df.empty:
            user_input_db = duplicate_df.at[0, "user_input"] or "-"
            kota_db = duplicate_df.at[0, "kota"] or "-"
            tgl_input_db = duplicate_df.at[0, "tgl_input"] or "-"

            return jsonify({
                "message": f"Link tersebut sudah pernah diinput oleh user '{user_input_db}' di cabang '{kota_db}' pada tanggal '{tgl_input_db}'"
            }), 400

        # Auto-fill user_update & tgl_update
        user_update = current_user
        tgl_update = datetime.now().date()

        # UPDATE
        query = """
            UPDATE dbo.inputan_link
            SET 
                medsos = ?,
                tema = ?,
                link = ?,
                user_update = ?,
                tgl_update = ?
            WHERE id = ?
        """

        with conn_dsn.cursor() as cursor:
            cursor.execute(query, (
                medsos,
                tema,
                link,
                user_update,
                tgl_update,
                id
            ))
            conn_dsn.commit()

        print("✅ INPUTAN UPDATED SUCCESS")

        return jsonify({
            "message": "Data berhasil diupdate"
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500

# ================= DELETE =================
@MenuInputan.route("/<int:id>", methods=["DELETE"])
@single_session_required
def delete_MenuInputan(id):
    conn_dsn = conn.dsn()
    current_user = get_jwt_identity()

    try:
        cursor = conn_dsn.cursor()
        cursor.execute("DELETE FROM dbo.inputan_link WHERE id = ?", (id,))
        conn_dsn.commit()
        cursor.close()

        return jsonify(
            logged_in_as=current_user,
            message="Data berhasil dihapus",
            id=id
        ), 200
    except Exception as e:
        return jsonify(message=str(e)), 500

