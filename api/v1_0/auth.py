from datetime import datetime
from flask import Blueprint, request, make_response
import bcrypt
from api.v1_0.security import verify_signature, decrypt_aes_base64, AES_PASSPHRASE, single_session_required

from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    get_jwt
)
import config.connection as conn

auth = Blueprint('auth', __name__)


# === VALIDASI TOKEN ===
@auth.route("/validate-token", methods=["GET"])
@single_session_required
def validate_token():
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    current_user = get_jwt_identity()
    return jsonify({"valid": True, "user": current_user}), 200


# === LOGIN ===
@auth.route("/login", methods=["POST"])
def login():
    try:
        username = request.json.get("username")
        ciphertext = request.json.get("password")
        iv = request.json.get("iv")

        plain_password = decrypt_aes_base64(ciphertext, iv, AES_PASSPHRASE)

        conn_dsn = conn.dsn()
        cursor = conn_dsn.cursor()
        cursor.execute("SELECT userid, password FROM dbo.user WHERE userid = ?", username)
        user = cursor.fetchone()

        if not user:
            return jsonify({"msg": "Bad userid or password"}), 401

        userid, stored_bcrypt = user

        if bcrypt.checkpw(plain_password.encode(), stored_bcrypt.encode()):

            cursor.execute("""
                        SELECT r.roleid
                        FROM dbo.cfg_role r
                        JOIN dbo.user ur ON r.roleid = ur.roleid 
                        WHERE ur.userid = ?
                    """, username)
            role_row = cursor.fetchone()
            role_name = role_row[0] if role_row else "user"

            # Masukkan user-agent atau device-id jika mau
            user_agent = request.headers.get("User-Agent")
            additional_claims = {
                "ua": user_agent,
                "role": role_name
            }

            access_token = create_access_token(
                identity=username,
                additional_claims=additional_claims
            )

            # Simpan token di DB
            cursor.execute("UPDATE dbo.user SET secret_key = ? WHERE userid = ?", (access_token, username))
            conn_dsn.commit()
            cursor.close()

            return jsonify(access_token=access_token), 200

        return jsonify({"msg": "Bad userid or password"}), 401

    except Exception as e:
        print("Error during login:", e)
        return jsonify({"msg": "Internal server error"}), 500



# === REGISTER ===
@auth.route("/register", methods=["POST"])
@single_session_required
def register():

    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    current_user = get_jwt_identity()

    userid = request.json.get("userid")
    username = request.json.get("username")
    password = request.json.get("password")
    roleid = request.json.get("roleid")
    amtfail = request.json.get("amtfail")
    lmtfail = request.json.get("lmtfail")
    kd_cabang = request.json.get("kd_cabang")
    no_hp = request.json.get("no_hp")
    tanggal_lahir = request.json.get("tanggal_lahir")
    jenis_kelamin = request.json.get("jenis_kelamin")

    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()

    cursor.execute("SELECT userid FROM dbo.user WHERE userid = ?", userid)
    existing_user = cursor.fetchone()
    if existing_user:
        return make_response(jsonify({"msg": f'Username "{userid}" already exists'}), 400)

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    cursor.execute("""
        INSERT INTO dbo.user (
           userid, username, password, roleid, amtfail, lmtfail, kd_cabang,
           no_hp, tanggal_lahir, jenis_kelamin, crtuser, crtdate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    userid, username, hashed_password, roleid, amtfail, lmtfail, kd_cabang,
    no_hp, tanggal_lahir, jenis_kelamin, current_user, datetime.now())

    conn_dsn.commit()
    return make_response(jsonify({"msg": "User created successfully"}), 201)


# === REFRESH TOKEN ===
@auth.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)

    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    cursor.execute("UPDATE dbo.user SET secret_key = ? WHERE userid = ?", access_token, identity)

    return jsonify(access_token=access_token)


# === PROTECTED TEST ===
@auth.route("/protected", methods=["GET"])
@single_session_required
def protected():

    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    current_user = get_jwt_identity()
    return jsonify({"msg": "Authorized", "user": current_user}), 200

# === LOGOUT ===
@auth.route("/logout", methods=["PUT"])
@jwt_required(verify_type=False)
def logout():
    try:
        # Validasi signature
        valid, msg = verify_signature()
        if not valid:
            return jsonify({"msg": msg}), 401

        # Ambil JWT dan tipe token
        token = get_jwt()
        ttype = token.get("type", "access")

        # Ambil identity user
        user_id = get_jwt_identity()

        # Update token di database
        conn_dsn = conn.dsn()
        cursor = conn_dsn.cursor()
        cursor.execute(
            "UPDATE dbo.user SET secret_key = NULL, lastlogin = ? WHERE userid = ?",
            datetime.now(), user_id
        )
        conn_dsn.commit()
        cursor.close()

        return jsonify(msg=f"{ttype.capitalize()} token successfully revoked"), 200

    except Exception as e:
        print("Error during logout:", e)
        return jsonify({"msg": "Internal server error"}), 500

# === GET CURRENT USER ===
@auth.route("/me", methods=["GET"])
@single_session_required
def me():
    username = get_jwt_identity()
    cursor = conn.dsn().cursor()
    cursor.execute("""
        SELECT A.userid, A.username, B.roleid || ' | ' || B.rolename AS rolename
        FROM dbo.user A
        INNER JOIN dbo.cfg_role B ON A.roleid = B.roleid
        WHERE A.userid = ?
    """, username)
    user = cursor.fetchone()
    if user:
        return jsonify({
            "userid": user[0],
            "username": user[1],
            "rolename": user[2],
        })
    return jsonify({"msg": "User not found"}), 404


# === ROLE MENU ===

import json
from flask import jsonify
import pandas as pd

@auth.route("/role_menu", methods=["GET"])
@single_session_required
def role_menu():
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401
    conn_dsn = conn.dsn()

    claims = get_jwt()
    role = claims.get("role", "user")

    query = """
    SELECT json_agg(menu_item) AS menu
FROM (
    SELECT
        rm.icon,
        rm.redirect_to AS "pageName",
        rm.menu_name AS title,
        (
            SELECT json_agg(
                json_build_object(
                    'icon', srm.icon,
                    'pageName', srm.redirect_to,
                    'title', srm.sub_menu_name,
                    'subMenu', (
                        SELECT json_agg(
                            json_build_object(
                                'icon', ss.icon,
                                'pageName', ss.redirect_to,
                                'title', ss.sub_sub_menu_name
                            )
                        )
                        FROM dbo.sub_sub_role_menu ss
                        INNER JOIN dbo.user_role_menu urm_ss
                            ON urm_ss.menu_id = ss.sub_sub_menu_id
                        WHERE ss.sub_menu_id = srm.sub_menu_id
                          AND urm_ss.roleid = ?
                    )
                )
            )
            FROM dbo.sub_role_menu srm
            INNER JOIN dbo.user_role_menu urm_srm
                ON urm_srm.menu_id = srm.sub_menu_id
            WHERE srm.menu_id = rm.menu_id
              AND urm_srm.roleid = ?
        ) AS "subMenu"
    FROM dbo.role_menu rm
    INNER JOIN dbo.user_role_menu urm_rm
        ON urm_rm.menu_id = rm.menu_id
    WHERE urm_rm.roleid = ?
    ORDER BY rm.menu_id
) AS menu_item
    """

    df = pd.read_sql(query, conn_dsn, params=[role, role, role])
    result = df.to_dict(orient="records")

    final_result = []
    if result and result[0]["menu"]:
        # Ambil data dari json_agg dan convert dari string JSON ke Python object
        menus = json.loads(result[0]["menu"]) if isinstance(result[0]["menu"], str) else result[0]["menu"]

        for item in menus:
            submenu = item.get("subMenu")
            if not submenu:
                item.pop("subMenu", None)
            else:
                for sub in submenu:
                    if not sub.get("subMenu"):
                        sub.pop("subMenu", None)
            final_result.append(item)

    return jsonify(final_result), 200

@auth.route("/wewenang_menu", methods=["GET"])
@single_session_required
def wewenang_menu():
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    conn_dsn = conn.dsn()
    claims = get_jwt()
    selected_role = request.args.get("roleid")
    if selected_role:
        role = selected_role
    else:
        role = claims.get("role", "user")

    query = """
    SELECT json_agg(
        json_build_object(
            'id', rm.menu_id,
            'name', rm.menu_name,
            'checked', CASE WHEN urm_rm.menu_id IS NULL THEN false ELSE true END,
            'children', COALESCE((
                SELECT json_agg(
                    json_build_object(
                        'id', srm.sub_menu_id,
                        'name', srm.sub_menu_name,
                        'checked', CASE WHEN urm_srm.menu_id IS NULL THEN false ELSE true END,
                        'children', COALESCE((
                            SELECT json_agg(
                                json_build_object(
                                    'id', ss.sub_sub_menu_id,
                                    'name', ss.sub_sub_menu_name,
                                    'checked', CASE WHEN urm_ss.menu_id IS NULL THEN false ELSE true END
                                )
                                ORDER BY ss.sub_sub_menu_id
                            )
                            FROM dbo.sub_sub_role_menu ss
                            LEFT JOIN dbo.user_role_menu urm_ss
                                ON ss.sub_sub_menu_id = urm_ss.menu_id
                                AND urm_ss.roleid = ?
                            WHERE ss.sub_menu_id = srm.sub_menu_id
                        ), '[]'::json)
                    )
                    ORDER BY srm.sub_menu_id
                )
                FROM dbo.sub_role_menu srm
                LEFT JOIN dbo.user_role_menu urm_srm
                    ON srm.sub_menu_id = urm_srm.menu_id
                    AND urm_srm.roleid = ?
                WHERE srm.menu_id = rm.menu_id
            ), '[]'::json)
        )
        ORDER BY rm.menu_id
    ) AS menu
    FROM dbo.role_menu rm
    LEFT JOIN dbo.user_role_menu urm_rm
        ON rm.menu_id = urm_rm.menu_id
        AND urm_rm.roleid = ?
    ;
    """

    df = pd.read_sql(query, conn_dsn, params=[role, role, role])
    result = df.to_dict(orient="records")

    final_result = []
    if result and result[0]["menu"]:
        menus = result[0]["menu"]
        if isinstance(menus, str):
            menus = json.loads(menus)
        final_result = menus

    return jsonify(final_result), 200



@auth.route("/wewenang_menu/save", methods=["POST"])
@single_session_required
def save_wewenang():
    data = request.get_json()

    roleid = data.get("roleid")
    menus = data.get("menus")

    conn_dsn = conn.dsn()
    cur = conn_dsn.cursor()



    try:
        # hapus dulu role lama
        cur.execute("""
            DELETE FROM dbo.user_role_menu
            WHERE roleid = ?
        """, (roleid,))

        # insert ulang yang checked
        for menu in menus:
            if menu.get("checked"):

                cur.execute("""
                    INSERT INTO dbo.user_role_menu (roleid, menu_id) VALUES(?, ?);
                """, (
                    roleid,
                    menu.get("id")
                ))

        conn_dsn.commit()

        return jsonify({
            "msg": "Berhasil simpan wewenang"
        })

    except Exception as e:
        conn_dsn.rollback()
        return jsonify({
            "msg": str(e)
        }), 500

    finally:
        cur.close()
        conn_dsn.close()

