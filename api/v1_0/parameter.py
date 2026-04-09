import json
from datetime import datetime

import bcrypt
from flask import Blueprint, jsonify, request, make_response
import pandas as pd
from flask_jwt_extended import jwt_required
import config.connection as conn
from flask_jwt_extended import get_jwt_identity

parameter = Blueprint('parameter', __name__)


@parameter.route("/user", methods=["GET"])
@jwt_required()
def user() :
    conn_dsn = conn.dsn()
    query_form = (
        f""" select a.userid, a.username, b.rolename as roleid, a.amtfail, a.lmtfail, a.no_hp, a.tanggal_lahir, a.kd_cabang 
        from dbo.user a left join dbo.cfg_role b on a.roleid = b.roleid""")
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200

@parameter.route("/deleteUser", methods=["DELETE"])
@jwt_required()
def deleteUser():
    conn_dsn = conn.dsn()
    cursor = conn.dsn()
    data = request.get_json()
    userid = data.get('userid')

    query = """ DELETE FROM dbo.user WHERE userid = ?  """
    params = [userid]

    try:
        cursor.execute(query, params)
        conn_dsn.commit()
        return jsonify({"message": "Data successfully deleted"}), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@parameter.route("/role", methods=["GET"])
@jwt_required()
def role() :
    conn_dsn = conn.dsn()
    query_form = (
        f""" select roleid, rolename from dbo.cfg_role """)
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200

@parameter.route("/cabang", methods=["GET"])
@jwt_required()
def cabang() :
    conn_dsn = conn.dsn()
    query_form = (
        f""" select kd_cab as kd_cabang, nm_cab from dbo.cfg_cabang """)
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200

@parameter.route("/user/<userid>", methods=["GET"])
@jwt_required()
def get_user_by_id(userid):
    conn_dsn = conn.dsn()
    query = """
        SELECT 
            a.userid, 
            a.username, 
            a.password,
            a.roleid, 
            a.amtfail, 
            a.lmtfail, 
            a.no_hp, 
            to_char(tanggal_lahir, 'YYYY-MM-DD') AS tanggal_lahir,
            a.kd_cabang, 
            a.jenis_kelamin
        FROM dbo.user a
        WHERE a.userid = ?
    """

    try:
        df = pd.read_sql(query, conn_dsn, params=[userid])
        if df.empty:
            return make_response(jsonify({"message": "User tidak ditemukan"}), 404)
        return jsonify(data=df.to_dict(orient="records")[0]), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@parameter.route("/user/update/<userid>", methods=["PUT"])
@jwt_required()
def update_user(userid):
    upduser = get_jwt_identity()
    update = datetime.now()
    conn_dsn = conn.dsn()
    data = request.json

    select_query = "SELECT password FROM dbo.user WHERE userid = ?"
    try:
        old_df = pd.read_sql(select_query, conn_dsn, params=[userid])
        if old_df.empty:
            return make_response(jsonify({"message": "User tidak ditemukan"}), 404)
        old_password = old_df.at[0, "password"]
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

    # Ambil data dari body
    username = data.get("username")
    password = data.get("password")  # bisa kosong atau None
    roleid = data.get("roleid")
    amtfail = data.get("amtfail")
    lmtfail = data.get("lmtfail")
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
            roleid = ?,
            amtfail = ?,
            lmtfail = ?,
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
                roleid,
                amtfail,
                lmtfail,
                no_hp,
                tanggal_lahir,
                kd_cabang,
                jenis_kelamin,
                upduser,
                update,
                userid

            ))
            conn_dsn.commit()
        return jsonify({"message": "User berhasil diupdate"}), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

@parameter.route("/user/profile", methods=["GET"])
@jwt_required()
def get_profil():
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
            a.kd_cabang, 
            a.jenis_kelamin
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
@jwt_required()
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


@parameter.route("/roleid", methods=["GET"])
@jwt_required()
def roleid():
    conn_dsn = conn.dsn()
    query_form = (
        f""" select roleid, rolename from dbo.cfg_role """)
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200

@parameter.route("/roleid", methods=["POST"])
@jwt_required()
def insert_roleid():
    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    data = request.json
    roleid = data.get("roleid")
    rolename = data.get("rolename")
    cursor.execute("select roleid from dbo.cfg_role where roleid = ?", roleid)
    existing_role = cursor.fetchone()
    if existing_role :
        return make_response(jsonify({"msg": f'Role "{roleid}" already exists'}), 400)
    cursor.execute("insert into dbo.cfg_role (roleid, rolename) VALUES( ?, ?)", roleid,rolename)

    conn_dsn.commit()
    return make_response(jsonify({"msg": "Role created successfully"}), 201)

@parameter.route("/roleid", methods=["PUT"])
@jwt_required()
def update_roleid():
    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    data = request.json
    roleid = data.get("roleid")
    rolename = data.get("rolename")

    cursor.execute("update dbo.cfg_role set rolename = ? where roleid = ?", rolename, roleid)

    conn_dsn.commit()
    return make_response(jsonify({"msg": "Role Update successfully"}), 201)

@parameter.route("/roleid", methods=["DELETE"])
@jwt_required()
def delete_roleid():
    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    data = request.json
    roleid = data.get("roleid")

    cursor.execute("delete from dbo.cfg_role where roleid = ?", roleid)

    conn_dsn.commit()
    return make_response(jsonify({"msg": "Role Delete successfully"}), 201)

@parameter.route("/roleid/<roleid>", methods=["GET"])
@jwt_required()
def rolebyid(roleid):
    conn_dsn = conn.dsn()
    query_form = (
        f""" select roleid, rolename from dbo.cfg_role where roleid = ? """)
    df = pd.read_sql(query_form, conn_dsn, params=[roleid])
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200

@parameter.route("/parentMenu", methods=["GET"])
@jwt_required()
def parent_menu():
    conn_dsn = conn.dsn()
    query_form = (
        f""" select * from dbo.role_menu """)
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200

@parameter.route("/parentMenu", methods=["POST"])
@jwt_required()
def insert_parent_menu():
    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    data = request.json

    menu_id = data.get("menu_id")
    menu_name = data.get("menu_name")
    icon = data.get("icon")
    redirect_to = data.get("redirect_to")

    cursor.execute("select menu_id from dbo.role_menu where menu_id = ?", menu_id)
    existing_role = cursor.fetchone()
    if existing_role:
        return make_response(jsonify({"msg": f'Menu Id "{menu_id}" already exists'}), 400)

    cursor.execute(" INSERT INTO dbo.role_menu (menu_id, menu_name, icon, redirect_to) VALUES(?,?,?,?)",
                   menu_id, menu_name, icon, redirect_to)

    conn_dsn.commit()
    return make_response(jsonify({"msg": "Parent Menu Insert successfully"}), 201)

@parameter.route("/parentMenu/<menuid>", methods=["GET"])
@jwt_required()
def parent_menuid(menuid):
    conn_dsn = conn.dsn()
    query_form = (
        f""" select * from dbo.role_menu where menu_id = ? """)
    df = pd.read_sql(query_form, conn_dsn, params=[menuid])
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200


@parameter.route("/parentMenu", methods=["PUT"])
@jwt_required()
def update_parent_menu():
    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    data = request.json
    menu_id = data.get("menu_id")
    menu_name = data.get("menu_name")
    icon = data.get("icon")
    redirect_to = data.get("redirect_to")

    cursor.execute("update dbo.role_menu set menu_name = ?, icon = ?, redirect_to = ? where menu_id = ?", menu_name, icon,redirect_to,menu_id  )

    conn_dsn.commit()
    return make_response(jsonify({"msg": "Parent Menu Update successfully"}), 201)

@parameter.route("/parentMenu", methods=["DELETE"])
@jwt_required()
def delete_parent_menu():
    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    data = request.json
    menu_id = data.get("menu_id")

    cursor.execute("delete from dbo.role_menu where menu_id = ?", menu_id)

    conn_dsn.commit()
    return make_response(jsonify({"msg": "Parent Menu Delete successfully"}), 201)


@parameter.route("/submenu", methods=["GET"])
@jwt_required()
def sub_menu():
    conn_dsn = conn.dsn()
    query_form = (
        f""" select b.menu_id, b.menu_name, a.* from dbo.sub_role_menu a
        inner join dbo.role_menu b on left(a.sub_menu_id, 1) = left(b.menu_id,1)
order by b.menu_id, a.sub_menu_id """)
    df = pd.read_sql(query_form, conn_dsn)
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200

@parameter.route("/submenu", methods=["POST"])
@jwt_required()
def insert_sub_menu():
    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    data = request.json

    sub_menu_id = data.get("sub_menu_id")
    sub_menu_name = data.get("sub_menu_name")
    icon = data.get("icon")
    redirect_to = data.get("redirect_to")

    cursor.execute("select sub_menu_id from dbo.sub_role_menu where sub_menu_id = ?", sub_menu_id)
    existing_role = cursor.fetchone()
    if existing_role:
        return make_response(jsonify({"msg": f'Sub Menu Id "{sub_menu_id}" already exists'}), 400)

    cursor.execute(" INSERT INTO dbo.sub_role_menu (sub_menu_id, sub_menu_name, icon, redirect_to) VALUES(?,?,?,?)",
                   sub_menu_id, sub_menu_name, icon, redirect_to)

    conn_dsn.commit()
    return make_response(jsonify({"msg": "Sub Menu Insert successfully"}), 201)

@parameter.route("/submenu/<sub_menu_id>", methods=["GET"])
@jwt_required()
def sub_menuid(sub_menu_id):
    conn_dsn = conn.dsn()
    query_form = (
        f""" select * from dbo.sub_role_menu where sub_menu_id = ? """)
    df = pd.read_sql(query_form, conn_dsn, params=[sub_menu_id])
    current_user = get_jwt_identity()
    result = df.to_dict(orient="records")
    return jsonify(logged_in_as=current_user, data=result), 200

@parameter.route("/submenu", methods=["PUT"])
@jwt_required()
def update_sub_menu():
    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    data = request.json
    sub_menu_id = data.get("sub_menu_id")
    sub_menu_name = data.get("sub_menu_name")
    icon = data.get("icon")
    redirect_to = data.get("redirect_to")

    cursor.execute("update dbo.sub_role_menu set sub_menu_name = ?, icon = ?, redirect_to = ? where sub_menu_id = ?", sub_menu_name, icon,redirect_to,sub_menu_id  )

    conn_dsn.commit()
    return make_response(jsonify({"msg": "Sub Menu Update successfully"}), 201)

@parameter.route("/submenu", methods=["DELETE"])
@jwt_required()
def delete_sub_menu():
    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    data = request.json
    sub_menu_id = data.get("sub_menu_id")

    cursor.execute("delete from dbo.sub_role_menu where sub_menu_id = ?", sub_menu_id)

    conn_dsn.commit()
    return make_response(jsonify({"msg": "Sub Menu Delete successfully"}), 201)

@parameter.route("/role_menu", methods=["POST"])
@jwt_required()
def role_menu():
    conn_dsn = conn.dsn()
    data = request.json
    roleid = data.get("roleid")

    update_query = """  
            SELECT
  rm.menu_id as id,
  rm.menu_name AS name,
  case when x.menu_id is null then 'false'
  else 'true' end as checked,
  COALESCE((
    SELECT JSON_AGG(
      JSON_BUILD_OBJECT(
      	'id', srm.sub_menu_id, 
        'name', srm.sub_menu_name,
        'checked', case when z.menu_id  is null then 'false' else 'true' end
      ) ORDER BY srm.sub_menu_id
    )
    FROM dbo.sub_role_menu srm
    left join dbo.user_role_menu z on srm.sub_menu_id = z.menu_id and z.roleid = ?
    WHERE LEFT(srm.sub_menu_id, 1) = LEFT(rm.menu_id, 1)
  ), '[]'::json) AS children
FROM dbo.role_menu rm
left join dbo.user_role_menu x on rm.menu_id = x.menu_id and x.roleid = ?
ORDER BY rm.menu_id
    """
    df = pd.read_sql(update_query, conn_dsn, params=[roleid, roleid] )
    result = df.to_dict(orient="records")
    for item in result:
        if isinstance(item.get("children"), str):
            try:
                item["children"] = json.loads(item["children"])
            except json.JSONDecodeError:
                item["children"] = None

    return jsonify(result), 200


@parameter.route('/insert_role_menu', methods=['POST'])
@jwt_required()
def insert_role_menu():
    data = request.get_json()
    roleid = data.get("roleid")
    menus = data.get("menus", [])  # list of dict: {menu_id: int, children: [...]}
    print(menus)

    if not roleid or not menus:
        return jsonify({"error": "roleid dan menus wajib diisi"}), 400

    try:
        db = conn.dsn()
        cursor = db.cursor()

        # Hapus semua role-menu sebelumnya
        cursor.execute("DELETE FROM dbo.user_role_menu WHERE roleid = ?", (roleid))

        # Insert semua menu dan submenu
        for menu in menus:
            menu_id = menu
            role = roleid
            if menu_id:
                cursor.execute(
                    "INSERT INTO dbo.user_role_menu (roleid, menu_id) VALUES (?, ?)",
                    (role, menu_id)
                )

        db.commit()
        return jsonify({"message": "Data berhasil disimpan."}), 200

    except Exception as e:
        db.rollback()
        print("Error:", e)
        return jsonify({"error": "Gagal menyimpan data."}), 500

    finally:
        cursor.close()
        db.close()
