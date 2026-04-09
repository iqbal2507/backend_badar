import json
from datetime import datetime

import bcrypt
from flask import Blueprint, jsonify, request, make_response
import pandas as pd
import config.connection as conn
from flask_jwt_extended import get_jwt_identity
from api.v1_0.security import verify_signature, single_session_required

parameter = Blueprint('parameter', __name__)

@parameter.route("/role", methods=["GET"])
@single_session_required
def role():
    conn_dsn = conn.dsn()
    query_form = (
        f""" select roleid , rolename from dbo.cfg_role  """)
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200

@parameter.route("/kecamatan", methods=["GET"])
@single_session_required
def kecamatan() :
    conn_dsn = conn.dsn()
    query_form = (
        f""" select upper(nama_value) as kecamatan from dbo.parameter_kecamatan """)
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200

@parameter.route("/user/profile", methods=["GET"])
@single_session_required
def get_profil():
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401
    conn_dsn = conn.dsn()
    user = get_jwt_identity()
    query = """
        SELECT 
            a.userid, 
            a.username, 
            a.password,
            a.amtfail, 
            a.lmtfail, 
            a.no_hp, 
            to_char(tanggal_lahir, 'YYYY-MM-DD') AS tanggal_lahir,
            a.jenis_kelamin,
            a.alamat,
            a.rt,
            a.rw,
            a.kecamatan,
            a.desa
        FROM dbo.user a
        WHERE a.userid = ?
    """

    try:
        df = pd.read_sql(query, conn_dsn, params=[user])
        if df.empty:
            return make_response(jsonify({"message": "User tidak ditemukan"}), 404)
        return jsonify(data=df.to_dict(orient="records")[0]), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

@parameter.route("/user/profile", methods=["PUT"])
@single_session_required
def update_profile():
    upduser = get_jwt_identity()
    update = datetime.now()
    conn_dsn = conn.dsn()
    data = request.json

    select_query = "SELECT password FROM dbo.user WHERE userid = ?"
    try:
        old_df = pd.read_sql(select_query, conn_dsn, params=[upduser])
        if old_df.empty:
            return make_response(jsonify({"message": "User tidak ditemukan"}), 404)
        old_password = old_df.at[0, "password"]
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

    # Ambil data dari body
    username = data.get("username")
    password = data.get("password")  # bisa kosong atau None
    # roleid = data.get("roleid")
    no_hp = data.get("no_hp")
    tanggal_lahir = data.get("tanggal_lahir")  # dalam format YYYY-MM-DD
    kd_cabang = data.get("kd_cabang")
    jenis_kelamin = data.get("jenis_kelamin")

    # Gunakan password lama jika tidak ada perubahan
    if not password or password == old_password:
        password_to_use = old_password
    else:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # Jika ingin hash di sini, bisa gunakan fungsi hash_password()
        password_to_use = hashed_password

    # Buat koneksi dan jalankan update
    update_query = """
        UPDATE dbo.user SET
            username = ?,
            password = ?,
            no_hp = ?,
            tanggal_lahir = ?,
            kd_cabang = ?,
            jenis_kelamin = ?,
            upduser = ?,
            upddate = ?
        WHERE userid = ?
    """

    try:
        with conn_dsn.cursor() as cursor:
            cursor.execute(update_query, (
                username,
                password_to_use,
                no_hp,
                tanggal_lahir,
                kd_cabang,
                jenis_kelamin,
                upduser,
                update,
                upduser

            ))
            conn_dsn.commit()
        return jsonify({"message": "User berhasil diupdate"}), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


