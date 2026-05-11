# api/v1_0/MenuUser.py

import bcrypt
from flask import Blueprint, jsonify, request, make_response, send_from_directory
import pandas as pd
import config.connection as conn
from flask_jwt_extended import get_jwt_identity
from api.v1_0.security import single_session_required
import os
import uuid

MenuUser = Blueprint('MenuUser', __name__)

# ================= FOLDER =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..", "uploads")
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= FILE =================
@MenuUser.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ================= GET ALL =================
@MenuUser.route("", methods=["GET"])
@single_session_required
def get_MenuUser():

    conn_dsn = conn.dsn()

    query = """
        SELECT
            userid,
            username,
            no_hp,
            tanggal_lahir,
            jenis_kelamin,
            alamat,
            provinsi,
            kota,
            kecamatan,
            desa,
            roleid,
            amtfail,
            lmtfail
        FROM dbo.user
        ORDER BY username ASC
    """

    df = pd.read_sql(query, conn_dsn)

    current_user = get_jwt_identity()

    result = df.to_dict(orient="records")

    return jsonify(
        logged_in_as=current_user,
        data=result
    ), 200

# ================= GET BY ID =================
# FIX: string bukan int
@MenuUser.route("/<string:id>", methods=["GET"])
@single_session_required
def get_MenuUser_by_id(id):

    conn_dsn = conn.dsn()

    query = """
        SELECT
            userid,
            username,
            no_hp,
            tanggal_lahir,
            jenis_kelamin,
            alamat,
            provinsi,
            kota,
            kecamatan,
            desa,
            roleid,
            amtfail,
            lmtfail
        FROM dbo.user
        WHERE userid = ?
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

        return jsonify(
            data=df.to_dict(orient="records")[0]
        ), 200

    except Exception as e:

        return make_response(
            jsonify({
                "error": str(e)
            }),
            500
        )

# ================= DELETE =================
# FIX: string bukan int
@MenuUser.route("/<string:id>", methods=["DELETE"])
@single_session_required
def delete_MenuUser(id):

    conn_dsn = conn.dsn()

    current_user = get_jwt_identity()

    try:

        cursor = conn_dsn.cursor()

        cursor.execute(
            "DELETE FROM dbo.user WHERE userid = ?",
            (id,)
        )

        conn_dsn.commit()

        cursor.close()

        return jsonify(
            logged_in_as=current_user,
            message="User berhasil dihapus",
            id=id
        ), 200

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500

# ================= CREATE =================
@MenuUser.route("", methods=["POST"])
@single_session_required
def create_MenuUser():

    try:

        print("🔥 CREATE USER START")

        conn_dsn = conn.dsn()

        data = request.form

        userid = data.get("userid")
        username = data.get("username")

        # password default = userid
        password = data.get("userid")

        no_hp = data.get("no_hp")
        tanggal_lahir = data.get("tanggal_lahir")
        kd_cabang = data.get("kd_cabang")
        jenis_kelamin = data.get("jenis_kelamin")
        alamat = data.get("alamat")
        kecamatan = data.get("kecamatan")
        desa = data.get("desa")
        provinsi = data.get("provinsi")
        kota = data.get("kota")
        roleid = data.get("roleid")

        amtfail = 0
        lmtfail = data.get("lmtfail")

        # ================= FILE =================
        file = request.files.get("file")

        filename = None

        if file:

            ext = os.path.splitext(file.filename)[1]

            filename = f"{uuid.uuid4()}{ext}"

            file.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    filename
                )
            )

        # ================= PASSWORD =================
        if password:

            hashed_password = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            )

            password_to_use = hashed_password.decode('utf-8')

        else:

            password_to_use = None

        # ================= VALIDASI =================
        if not userid or not username:

            return jsonify({
                "message": "userid & username wajib diisi"
            }), 400

        # ================= INSERT =================
        query = """
            INSERT INTO dbo.user
            (
                userid,
                username,
                password,
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
                roleid,
                amtfail,
                lmtfail
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """

        with conn_dsn.cursor() as cursor:

            cursor.execute(query, (
                userid,
                username,
                password_to_use,
                no_hp,
                tanggal_lahir,
                kd_cabang,
                jenis_kelamin,
                alamat,
                kecamatan,
                desa,
                filename,
                provinsi,
                kota,
                roleid,
                amtfail,
                lmtfail
            ))

            conn_dsn.commit()

        return jsonify({
            "message": "User berhasil ditambahkan"
        }), 201

    except Exception as e:

        import traceback
        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500


# ================= UPDATE =================
@MenuUser.route("/update/<string:id>", methods=["PUT"])
@single_session_required
def update_MenuUser(id):

    try:

        print("🔥 UPDATE USER")

        conn_dsn = conn.dsn()

        data = request.form

        username = data.get("username")
        no_hp = data.get("no_hp")
        tanggal_lahir = data.get("tanggal_lahir")
        jenis_kelamin = data.get("jenis_kelamin")
        alamat = data.get("alamat")
        provinsi = data.get("provinsi")
        kota = data.get("kota")
        roleid = data.get("roleid")
        lmtfail = data.get("lmtfail")

        query = """
            UPDATE dbo.user
            SET
                username = ?,
                no_hp = ?,
                tanggal_lahir = ?,
                jenis_kelamin = ?,
                alamat = ?,
                provinsi = ?,
                kota = ?,
                roleid = ?,
                lmtfail = ?
            WHERE userid = ?
        """

        with conn_dsn.cursor() as cursor:

            cursor.execute(query, (
                username,
                no_hp,
                tanggal_lahir,
                jenis_kelamin,
                alamat,
                provinsi,
                kota,
                roleid,
                lmtfail,
                id
            ))

            conn_dsn.commit()

        return jsonify({
            "message": "User berhasil diupdate"
        }), 200

    except Exception as e:

        import traceback
        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500

# ================= RESET PASSWORD =================
@MenuUser.route("/action/reset-password/<string:id>", methods=["PUT"])
@single_session_required
def reset_password(id):

    print("🔥 RESET PASSWORD MASUK")
    print("USER ID:", id)

    try:

        conn_dsn = conn.dsn()

        new_password = id

        hashed_password = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        query = """
            UPDATE dbo.user
            SET password = ?
            WHERE userid = ?
        """

        with conn_dsn.cursor() as cursor:

            cursor.execute(query, (
                hashed_password,
                id
            ))

            conn_dsn.commit()

        return jsonify({
            "message": "Password berhasil direset",
            "userid": id
        }), 200

    except Exception as e:

        import traceback
        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500

