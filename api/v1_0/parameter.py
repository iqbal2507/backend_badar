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
def kecamatan():
    conn_dsn = conn.dsn()
    query_form = """
        SELECT 
            param_value, 
            UPPER(nama_value) AS nama_value, 
            join_value 
        FROM dbo.parameter_kecamatan
    """
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200

@parameter.route("/desa", methods=["GET"])
@single_session_required
def desa():
    conn_dsn = conn.dsn()
    query_form = """
        SELECT 
            param_value, 
            UPPER(nama_value) AS nama_value, 
            join_value 
        FROM dbo.parameter_desa
    """
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200



@parameter.route("/provinsi", methods=["GET"])
@single_session_required
def provinsi():
    conn_dsn = conn.dsn()
    query_form = """
        SELECT 
            param_value, 
            UPPER(nama_value) AS nama_value, 
            join_value 
        FROM dbo.parameter_provinsi
    """
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200

@parameter.route("/kota", methods=["GET"])
@single_session_required
def kota():
    conn_dsn = conn.dsn()
    query_form = """
        SELECT 
            param_value, 
            UPPER(nama_value) AS nama_value, 
            join_value 
        FROM dbo.parameter_kota
    """
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200


@parameter.route("/tema", methods=["GET"])
@single_session_required
def tema():
    conn_dsn = conn.dsn()
    query_form = """
        SELECT 
            param_value, 
            UPPER(nama_value) AS nama_value, 
            join_value 
        FROM dbo.parameter_tema
    """
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200


@parameter.route("/sosmed", methods=["GET"])
@single_session_required
def sosmed():
    conn_dsn = conn.dsn()
    query_form = """
        SELECT 
            param_value, 
            UPPER(nama_value) AS nama_value, 
            join_value 
        FROM dbo.parameter_sosmed
    """
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200


@parameter.route("/wilayah-input", methods=["GET"])
@single_session_required
def wilayah_monitoring():

    conn_dsn = conn.dsn()

    query = """
        SELECT DISTINCT
            u.kota AS nama_value
        FROM dbo.inputan_link mm
        LEFT JOIN dbo.user u
            ON u.userid = mm.user_input
        WHERE u.kota IS NOT NULL
        ORDER BY u.kota
    """

    df = pd.read_sql(query, conn_dsn)

    result = df.to_dict(orient="records")

    return jsonify(data=result), 200

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
            a.desa,
            a.file,
            a.provinsi,
            a.kota
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


    print("MASUK FUNCTION")

    print("CONTENT TYPE:", request.content_type)

    print("REQUEST JSON:", request.json)

    print("REQUEST FORM:", request.form)


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
    alamat = data.get("alamat")
    kecamatan = data.get("kecamatan")
    desa = data.get("desa")
    file = data.get("file")
    provinsi = data.get("provinsi")
    kota = data.get("kota")
    userid = get_jwt_identity()

    print("CONTENT TYPE:", request.content_type)
    print("FILES:", request.files)
    print("FORM:", request.form)

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
            alamat = ?,
            kecamatan = ?,
            desa = ?,
            file = ?,
            provinsi = ?,
            kota = ?,
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
                alamat,
                kecamatan,
                desa,
                file,
                provinsi,
                kota,
                upduser,
                update,
                userid

            ))
            conn_dsn.commit()



        return jsonify({"message": "User berhasil diupdate"}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return make_response(jsonify({"error": str(e)}), 500)


