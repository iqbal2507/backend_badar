# api/v1_0/MenuKegiatan.py
import json
from datetime import datetime
# api/v1_0/MenuKegiatan.py
import json
from datetime import datetime
from flask import Blueprint, jsonify, request, make_response, send_from_directory
import pandas as pd
import config.connection as conn
from flask_jwt_extended import get_jwt_identity
from api.v1_0.security import single_session_required
import os, uuid

MenuKegiatan = Blueprint('MenuKegiatan', __name__)

# ✅ FIX: pakai 1 variable saja
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "uploads"))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ endpoint akses file
@MenuKegiatan.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ================= GET =================
@MenuKegiatan.route("", methods=["GET"])
@single_session_required
def get_MenuKegiatan():
    conn_dsn = conn.dsn()
    query = """
        SELECT  
            id, kegiatan,tgl_kegiatan, alamat, keterangan, file1, file2, file3
        FROM dbo.kegiatan
        ORDER BY id DESC
    """
    try:
        df = pd.read_sql(query, conn_dsn)
        return jsonify(data=df.to_dict(orient="records")), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@MenuKegiatan.route("/<int:id>", methods=["GET"])
@single_session_required
def get_MenuKegiatan_by_id(id):
    conn_dsn = conn.dsn()
    query = """
        SELECT 
            id, kegiatan,tgl_kegiatan, alamat, keterangan, file1,file2,file3
        FROM dbo.kegiatan
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
@MenuKegiatan.route("", methods=["POST"])
@single_session_required
def add_MenuKegiatan():
    conn_dsn = conn.dsn()

    # ambil form
    kegiatan = request.form.get("kegiatan")
    tgl_kegiatan = request.form.get("tgl_kegiatan")
    alamat = request.form.get("alamat")
    keterangan = request.form.get("keterangan")

    # file
    file1 = request.files.get("foto1")
    filename1 = None

    file2 = request.files.get("foto2")
    filename2 = None

    file3 = request.files.get("foto3")
    filename3 = None

    if file1:
        filename1 = str(uuid.uuid4()) + "_" + file1.filename
        filepath1 = os.path.join(UPLOAD_FOLDER, filename1)
        file1.save(filepath1)

    if file2:
        filename2 = str(uuid.uuid4()) + "_" + file2.filename
        filepath2 = os.path.join(UPLOAD_FOLDER, filename2)
        file2.save(filepath2)

    if file3:
        filename3 = str(uuid.uuid4()) + "_" + file3.filename
        filepath3 = os.path.join(UPLOAD_FOLDER, filename3)
        file3.save(filepath3)

    query = """
        INSERT INTO dbo.kegiatan 
        ( kegiatan, tgl_kegiatan, alamat, keterangan, file1, file2, file3)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    try:
        with conn_dsn.cursor() as cursor:
            cursor.execute(query, (
                kegiatan,tgl_kegiatan, alamat, keterangan, filename1,filename2,filename3
            ))
            conn_dsn.commit()

        return jsonify({"message": "Data berhasil ditambahkan"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# PUT - Update data MenuKegiatan
@MenuKegiatan.route("/<int:id>", methods=["PUT"])
@single_session_required
def update_MenuKegiatan(id):
    conn_dsn = conn.dsn()

    kegiatan = request.form.get("kegiatan")
    tgl_kegiatan = request.form.get("tgl_kegiatan")
    alamat = request.form.get("alamat")
    keterangan = request.form.get("keterangan")

    file1 = request.files.get("foto1")
    filename1 = None

    file2 = request.files.get("foto2")
    filename2 = None

    file3 = request.files.get("foto3")
    filename3 = None

    if file1:
        filename1 = str(uuid.uuid4()) + "_" + file1.filename
        filepath1 = os.path.join(UPLOAD_FOLDER, filename1)
        file1.save(filepath1)

    if file2:
        filename2 = str(uuid.uuid4()) + "_" + file2.filename
        filepath2 = os.path.join(UPLOAD_FOLDER, filename2)
        file2.save(filepath2)

    if file3:
        filename3 = str(uuid.uuid4()) + "_" + file3.filename
        filepath3 = os.path.join(UPLOAD_FOLDER, filename3)
        file3.save(filepath3)

    update_query = """
        UPDATE dbo.kegiatan SET
            kegiatan = ?,
            tgl_kegiatan = ?,
            alamat = ?,
            keterangan = ?,
            file1 = COALESCE(?, file1),
            file2 = COALESCE(?, file2),
            file3 = COALESCE(?, file3)
        WHERE id = ?
    """

    try:
        with conn_dsn.cursor() as cursor:
            cursor.execute(update_query, (
                kegiatan, tgl_kegiatan, alamat, keterangan, filename1, filename2, filename3, id
            ))
            conn_dsn.commit()
        return jsonify({"message": "Data berhasil diupdate"}), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


# DELETE - Hapus data MenuKegiatan
@MenuKegiatan.route("/<int:id>", methods=["DELETE"])
@single_session_required
def delete_MenuKegiatan(id):
    current_user = get_jwt_identity()
    conn_dsn = conn.dsn()

    # Cek apakah data exists
    select_query = "SELECT id FROM dbo.kegiatan WHERE id = ?"
    try:
        df = pd.read_sql(select_query, conn_dsn, params=[id])
        if df.empty:
            return make_response(jsonify({"message": "Data MenuKegiatan tidak ditemukan"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

    delete_query = "DELETE FROM dbo.kegiatan WHERE id = ?"

    try:
        with conn_dsn.cursor() as cursor:
            cursor.execute(delete_query, (id,))
            conn_dsn.commit()
        return jsonify({"message": "Data MenuKegiatan berhasil dihapus"}), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

