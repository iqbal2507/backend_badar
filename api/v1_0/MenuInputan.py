# api/v1_0/MenuInputan.py
import json
from datetime import datetime
from flask import Blueprint, jsonify, request, make_response
import pandas as pd
import config.connection as conn
from flask_jwt_extended import get_jwt_identity
from api.v1_0.security import single_session_required

MenuInputan = Blueprint('MenuInputan', __name__)


# ================= GET ALL =================
@MenuInputan.route("", methods=["GET"])
@single_session_required
def get_MenuInputan():
    conn_dsn = conn.dsn()
    query = """
        SELECT 
            id,
            medsos,
            tema,
            link,
            username,
            user_input,
            tgl_input,
            user_update,
            tgl_update
        FROM dbo.inputan_link
        ORDER BY tgl_input DESC
    """
    df = pd.read_sql(query, conn_dsn)

    # Convert date columns to string
    if 'tgl_input' in df.columns:
        df['tgl_input'] = df['tgl_input'].astype(str)
    if 'tgl_update' in df.columns:
        df['tgl_update'] = df['tgl_update'].astype(str)

    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200


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
            username,
            user_input,
            tgl_input,
            user_update,
            tgl_update
        FROM dbo.inputan_link
        WHERE id = ?
    """
    try:
        df = pd.read_sql(query, conn_dsn, params=[id])

        if df.empty:
            return jsonify({"message": "Data tidak ditemukan"}), 404

        # Convert date to string
        if 'tgl_input' in df.columns:
            df['tgl_input'] = df['tgl_input'].astype(str)
        if 'tgl_update' in df.columns:
            df['tgl_update'] = df['tgl_update'].astype(str)

        return jsonify(data=df.to_dict(orient="records")[0]), 200

    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


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
        username = data.get("username")

        # Validasi
        if not medsos or not link:
            return jsonify({"message": "medsos & link wajib diisi"}), 400

        # Auto-fill user_input & tgl_input
        user_input = current_user
        tgl_input = datetime.now().date()

        # INSERT
        query = """
            INSERT INTO dbo.inputan_link
            (medsos, tema, link, username, user_input, tgl_input)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        with conn_dsn.cursor() as cursor:
            cursor.execute(query, (
                medsos,
                tema,
                link,
                username,
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
        username = data.get("username")

        # Validasi
        if not medsos or not link:
            return jsonify({"message": "medsos & link wajib diisi"}), 400

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
                username = ?,
                user_update = ?,
                tgl_update = ?
            WHERE id = ?
        """

        with conn_dsn.cursor() as cursor:
            cursor.execute(query, (
                medsos,
                tema,
                link,
                username,
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