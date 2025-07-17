import json
from datetime import datetime

import pandas as pd
from flask import Blueprint, make_response
from flask import jsonify
from flask import request
import bcrypt

from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, get_jwt, \
    JWTManager
import config.connection as conn

auth = Blueprint('auth', __name__)


@auth.route("/login", methods=["POST"])
def login():
    username = request.json.get("username")
    password = request.json.get("password")

    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    cursor.execute("select userid, password from dbo.user where userid = ?", username)
    user = cursor.fetchone()
    if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)

        cursor = conn_dsn.cursor()
        cursor.execute("update dbo.user set secret_key = ? where userid = ?", access_token, username)

        return jsonify(access_token=access_token, refresh_token=refresh_token)
    else :
        cursor.execute("update dbo.user set amtfail = amtfail + 1 where userid = ?", username)
        return jsonify({"msg": "Bad userid or password"}), 401

@auth.route("/register", methods=["POST"] )
@jwt_required()
def register():
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
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute("INSERT INTO dbo.user (userid, username, password, roleid, amtfail, lmtfail, kd_cabang, no_hp, tanggal_lahir, jenis_kelamin, crtuser, crtdate) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   userid, username, hashed_password.decode('utf-8'), roleid, amtfail, lmtfail, kd_cabang, no_hp, tanggal_lahir, jenis_kelamin, current_user, datetime.now())
    conn_dsn.commit()
    return make_response(jsonify({"msg": "User created successfully"}), 201)

@auth.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)

    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    cursor.execute("update dbo.user set secret_key = ? where userid = ?", access_token, identity)

    return jsonify(access_token=access_token)

@auth.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


@auth.route("/logout", methods=["DELETE"])
@jwt_required(verify_type=False)
def logout():
    token = get_jwt()
    ttype = token["type"]

    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()

    cursor.execute("update dbo.user set secret_key = null, lastlogin = ? where userid = ?", datetime.now(), get_jwt_identity())

    return jsonify(msg=f"{ttype.capitalize()} token successfully revoked")

@auth.route("/me", methods=["GET"])
@jwt_required()
def me():
    username = get_jwt_identity()
    cursor = conn.dsn().cursor()
    cursor.execute("SELECT userid, username FROM dbo.user WHERE userid = ?", username)
    user = cursor.fetchone()
    if user:
        return jsonify({
            "userid": user[0],
            "username": user[1]
        })
    return jsonify({"msg": "User not found"}), 404

@auth.route("/role_menu", methods=["GET"])
@jwt_required()
def role_menu():
    username = get_jwt_identity()
    conn_dsn = conn.dsn()

    query = """
    SELECT
  rm.menu_id,
  rm.menu_name AS title,
  rm.icon,
  rm.redirect_to AS to,
  COALESCE((
    SELECT JSON_AGG(
      JSON_BUILD_OBJECT(
        'title', srm.sub_menu_name,
        'icon', srm.icon,
        'to', srm.redirect_to
      )
    )
    FROM dbo.sub_role_menu srm
    JOIN dbo.user_role_menu urm_sub ON urm_sub.menu_id = srm.sub_menu_id
    WHERE LEFT(srm.sub_menu_id, 1) = LEFT(rm.menu_id, 1)
      AND urm_sub.roleid = urm.roleid
  ), '[]'::json) AS children
FROM dbo.role_menu rm
JOIN dbo.user_role_menu urm ON urm.menu_id = rm.menu_id
WHERE urm.roleid = (SELECT roleid FROM dbo."user" WHERE userid = ?)
ORDER BY rm.menu_id;


    """

    df = pd.read_sql(query, conn_dsn, params=[username])

    # Convert stringified JSON array to Python list if needed
    result = df.to_dict(orient="records")
    for item in result:
        if isinstance(item.get("children"), str):
            try:
                item["children"] = json.loads(item["children"])
            except json.JSONDecodeError:
                item["children"] = None

    return jsonify(result), 200
