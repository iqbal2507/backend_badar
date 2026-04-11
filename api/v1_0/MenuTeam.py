# api/v1_0/MenuMenuTeam.py
import json
from datetime import datetime
# api/v1_0/MenuMenuTeam.py
import json
from datetime import datetime
from flask import Blueprint, jsonify, request, make_response, send_from_directory
import pandas as pd
import config.connection as conn
from flask_jwt_extended import get_jwt_identity
from api.v1_0.security import single_session_required
import os, uuid

MenuTeam = Blueprint('MenuTeam', __name__)

# ✅ FIX: pakai 1 variable saja
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "uploads"))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ endpoint akses file
@MenuTeam.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ================= GET =================
@MenuTeam.route("", methods=["GET"])
@single_session_required
def get_MenuTeam():
    conn_dsn = conn.dsn()
    query = """
        SELECT 
            id, userid, username, alamat, nik, no_hp,
            jabatan, kecamatan, desa, keterangan, file
        FROM dbo.team
        ORDER BY id DESC
    """
    try:
        df = pd.read_sql(query, conn_dsn)
        return jsonify(data=df.to_dict(orient="records")), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@MenuTeam.route("/<int:id>", methods=["GET"])
@single_session_required
def get_MenuTeam_by_id(id):
    conn_dsn = conn.dsn()
    query = """
        SELECT 
            id, userid, username, alamat, nik, no_hp,
            jabatan, kecamatan, desa, keterangan, file
        FROM dbo.team
        WHERE id = ?
    """
    try:
        df = pd.read_sql(query, conn_dsn, params=[id])

        if df.empty:
            return jsonify({"message": "Data tidak ditemukan"}), 404

        return jsonify(data=df.to_dict(orient="records")[0]), 200

    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# ================= POST =================
@MenuTeam.route("", methods=["POST"])
@single_session_required
def add_MenuTeam():
    conn_dsn = conn.dsn()

    # ambil form
    userid = request.form.get("userid")
    username = request.form.get("username")
    alamat = request.form.get("alamat")
    nik = request.form.get("nik")
    no_hp = request.form.get("no_hp")
    jabatan = request.form.get("jabatan")
    kecamatan = request.form.get("kecamatan")
    desa = request.form.get("desa")
    keterangan = request.form.get("keterangan")

    # file
    file = request.files.get("foto")
    filename = None

    if file:
        filename = str(uuid.uuid4()) + "_" + file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

    if not userid or not username:
        return jsonify({"message": "User ID dan Username harus diisi"}), 400

    query = """
        INSERT INTO dbo.team 
        (userid, username, alamat, nik, no_hp, jabatan, kecamatan, desa, keterangan, file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        with conn_dsn.cursor() as cursor:
            cursor.execute(query, (
                userid, username, alamat, nik, no_hp,
                jabatan, kecamatan, desa, keterangan, filename
            ))
            conn_dsn.commit()

        return jsonify({"message": "Data berhasil ditambahkan"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# PUT - Update data MenuTeam
@MenuTeam.route("/<int:id>", methods=["PUT"])
@single_session_required
def update_MenuTeam(id):
    conn_dsn = conn.dsn()

    userid = request.form.get("userid")
    username = request.form.get("username")
    alamat = request.form.get("alamat")
    nik = request.form.get("nik")
    no_hp = request.form.get("no_hp")
    jabatan = request.form.get("jabatan")
    kecamatan = request.form.get("kecamatan")
    desa = request.form.get("desa")
    keterangan = request.form.get("keterangan")

    file = request.files.get("foto")
    filename = None

    if file:
        filename = str(uuid.uuid4()) + "_" + file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

    update_query = """
        UPDATE dbo.team SET
            userid = ?,
            username = ?,
            alamat = ?,
            nik = ?,
            no_hp = ?,
            jabatan = ?,
            kecamatan = ?,
            desa = ?,
            keterangan = ?,
            file = COALESCE(?, file)
        WHERE id = ?
    """

    try:
        with conn_dsn.cursor() as cursor:
            cursor.execute(update_query, (
                userid, username, alamat, nik, no_hp,
                jabatan, kecamatan, desa, keterangan,
                filename, id
            ))
            conn_dsn.commit()
        return jsonify({"message": "Data berhasil diupdate"}), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


# DELETE - Hapus data MenuTeam
@MenuTeam.route("/<int:id>", methods=["DELETE"])
@single_session_required
def delete_MenuTeam(id):
    current_user = get_jwt_identity()
    conn_dsn = conn.dsn()

    # Cek apakah data exists
    select_query = "SELECT id FROM dbo.team WHERE id = ?"
    try:
        df = pd.read_sql(select_query, conn_dsn, params=[id])
        if df.empty:
            return make_response(jsonify({"message": "Data MenuTeam tidak ditemukan"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

    delete_query = "DELETE FROM dbo.team WHERE id = ?"

    try:
        with conn_dsn.cursor() as cursor:
            cursor.execute(delete_query, (id,))
            conn_dsn.commit()
        return jsonify({"message": "Data MenuTeam berhasil dihapus"}), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

