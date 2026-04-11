# api/v1_0/MenuMenuTeam.py
import json
from datetime import datetime
from flask import Blueprint, jsonify, request, make_response
import pandas as pd
import config.connection as conn
from flask_jwt_extended import get_jwt_identity
from api.v1_0.security import verify_signature, single_session_required

MenuTeam = Blueprint('MenuTeam', __name__)


# GET - Ambil semua data MenuTeam
@MenuTeam.route("", methods=["GET"])
@single_session_required
def get_MenuTeam():
    conn_dsn = conn.dsn()
    query = """
        SELECT 
            id,
            userid,
            username,
            alamat,
            nik,
            no_hp,
            jabatan,
            keterangan
        FROM dbo.team
        ORDER BY id DESC
    """

    try:
        df = pd.read_sql(query, conn_dsn)
        current_user = get_jwt_identity()
        result = df.to_dict(orient="records")
        return jsonify(logged_in_as=current_user, data=result), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


# GET - Ambil data MenuTeam by ID
@MenuTeam.route("/<int:id>", methods=["GET"])
@single_session_required
def get_MenuTeam_by_id(id):
    conn_dsn = conn.dsn()
    query = """
        SELECT 
            id,
            userid,
            username,
            alamat,
            nik,
            no_hp,
            jabatan,
            keterangan
        FROM dbo.team
        WHERE id = ?
    """

    try:
        df = pd.read_sql(query, conn_dsn, params=[id])
        if df.empty:
            return make_response(jsonify({"message": "Data MenuTeam tidak ditemukan"}), 404)

        current_user = get_jwt_identity()
        result = df.to_dict(orient="records")[0]
        return jsonify(logged_in_as=current_user, data=result), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


# POST - Tambah data MenuTeam
@MenuTeam.route("", methods=["POST"])
@single_session_required
def add_MenuTeam():
    current_user = get_jwt_identity()
    conn_dsn = conn.dsn()
    data = request.json

    # Ambil data dari body
    userid = data.get("userid")
    username = data.get("username")
    alamat = data.get("alamat")
    nik = data.get("nik")
    no_hp = data.get("no_hp")
    jabatan = data.get("jabatan")
    keterangan = data.get("keterangan")

    # Validasi data wajib
    if not userid or not username:
        return make_response(jsonify({"message": "User ID dan Username harus diisi"}), 400)

    insert_query = """
        INSERT INTO dbo.team (userid, username, alamat, nik, no_hp, jabatan, keterangan)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    try:
        with conn_dsn.cursor() as cursor:
            cursor.execute(insert_query, (
                userid,
                username,
                alamat,
                nik,
                no_hp,
                jabatan,
                keterangan
            ))
            conn_dsn.commit()
        return jsonify({"message": "Data MenuTeam berhasil ditambahkan"}), 201
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


# PUT - Update data MenuTeam
@MenuTeam.route("/<int:id>", methods=["PUT"])
@single_session_required
def update_MenuTeam(id):
    current_user = get_jwt_identity()
    conn_dsn = conn.dsn()
    data = request.json

    # Cek apakah data exists
    select_query = "SELECT id FROM dbo.team WHERE id = ?"
    try:
        df = pd.read_sql(select_query, conn_dsn, params=[id])
        if df.empty:
            return make_response(jsonify({"message": "Data MenuTeam tidak ditemukan"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

    # Ambil data dari body
    userid = data.get("userid")
    username = data.get("username")
    alamat = data.get("alamat")
    nik = data.get("nik")
    no_hp = data.get("no_hp")
    jabatan = data.get("jabatan")
    keterangan = data.get("keterangan")

    # Validasi data wajib
    if not userid or not username:
        return make_response(jsonify({"message": "User ID dan Username harus diisi"}), 400)

    update_query = """
        UPDATE dbo.team SET
            userid = ?,
            username = ?,
            alamat = ?,
            nik = ?,
            no_hp = ?,
            jabatan = ?,
            keterangan = ?
        WHERE id = ?
    """

    try:
        with conn_dsn.cursor() as cursor:
            cursor.execute(update_query, (
                userid,
                username,
                alamat,
                nik,
                no_hp,
                jabatan,
                keterangan,
                id
            ))
            conn_dsn.commit()
        return jsonify({"message": "Data MenuTeam berhasil diupdate"}), 200
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