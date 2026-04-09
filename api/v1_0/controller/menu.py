from api.v1_0.security import verify_signature, single_session_required
from flask import Blueprint, jsonify, request, make_response
import pandas as pd
import config.connection as conn
menu = Blueprint('menu', __name__)


# parameter Parent Menu
@menu.route("/parent-menu", methods=["GET"])
@single_session_required
def parent_menu():
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401
    conn_dsn = conn.dsn()

    query = f""" select 
                    id,
                    menu_id, menu_name as title, icon, 
                    redirect_to as "pageName"
                 from
	                dbo.role_menu """

    df = pd.read_sql(query, conn_dsn)
    result = df.to_dict(orient="records")
    return jsonify(result), 200


@menu.route("/parent-menu/<int:id>", methods=["DELETE"])
@single_session_required
def parent_menu_delete(id):
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    conn_dsn = conn.dsn()
    try:
        cursor = conn_dsn.cursor()
        query = "DELETE FROM dbo.role_menu WHERE id = ?"
        cursor.execute(query, (id,))
        conn_dsn.commit()
        cursor.close()

        return jsonify({"id": id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@menu.route("/parent-menu/<int:id>", methods=["GET"])
@single_session_required
def parent_menu_by_id(id):
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    conn_dsn = conn.dsn()
    query = """
        SELECT 
            id, menu_id, menu_name AS title, icon, redirect_to AS "pageName"
        FROM dbo.role_menu
        WHERE id = ?
    """

    df = pd.read_sql(query, conn_dsn, params=[id])
    result = df.to_dict(orient="records")
    return jsonify(result), 200


@menu.route("/parent-menu/<int:id>", methods=["PUT"])
@single_session_required
def parent_menu_update(id):

    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    menu_id = request.json.get("menu_id")
    title = request.json.get("title")
    icon = request.json.get("icon")
    pageName = request.json.get("pageName")

    cursor.execute("SELECT menu_id FROM dbo.role_menu WHERE menu_id = ?", menu_id)
    existing_role = cursor.fetchone()
    if not existing_role:
        return make_response(jsonify({"msg": f'menu_id "{menu_id}" Tidak Ada'}), 400)
    try:
        cursor = conn_dsn.cursor()
        query = "UPDATE DBO.role_menu SET menu_name = ?, icon = ?, redirect_to = ? WHERE id = ?"
        cursor.execute(query, (title, icon, pageName, id))
        conn_dsn.commit()
        cursor.close()

        return jsonify({"id": id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@menu.route("/parent-menu", methods=["POST"])
@single_session_required
def parent_menu_add():

    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    menu_id = request.json.get("menu_id")
    title = request.json.get("title")
    icon = request.json.get("icon")
    pageName = request.json.get("pageName")

    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()

    cursor.execute("SELECT menu_id FROM dbo.role_menu WHERE menu_id = ?", menu_id)
    existing_user = cursor.fetchone()
    if existing_user:
        return make_response(jsonify({"msg": f'Menu Id "{menu_id}" already exists'}), 400)

    cursor.execute("""
        INSERT INTO dbo.role_menu (
           menu_id, menu_name, icon, redirect_to
        ) VALUES (?, ?, ?, ?)
    """,
    menu_id, title, icon, pageName)

    conn_dsn.commit()
    return make_response(jsonify({"msg": "Role Menu created successfully"}), 201)

# Parameter Sub Menu
@menu.route("/sub-menu", methods=["GET"])
@single_session_required
def sub_menu():
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401
    conn_dsn = conn.dsn()

    query = f""" select 
                    id,
                    menu_id, 
                    sub_menu_id,
                    sub_menu_name as title, icon, 
                    redirect_to as "pageName"
                 from
	                dbo.sub_role_menu order by menu_id"""

    df = pd.read_sql(query, conn_dsn)
    result = df.to_dict(orient="records")
    return jsonify(result), 200


@menu.route("/sub-menu/<int:id>", methods=["GET"])
@single_session_required
def sub_menu_by_id(id):
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    conn_dsn = conn.dsn()
    query = """
        SELECT 
            id, menu_id, sub_menu_id, sub_menu_name AS title, icon, redirect_to AS "pageName"
        FROM dbo.sub_role_menu
        WHERE id = ?
    """
    df = pd.read_sql(query, conn_dsn, params=[id])
    result = df.to_dict(orient="records")
    return jsonify(result), 200


@menu.route("/sub-menu/<int:id>", methods=["DELETE"])
@single_session_required
def sub_menu_delete(id):
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    conn_dsn = conn.dsn()
    try:
        cursor = conn_dsn.cursor()
        query = "DELETE FROM dbo.sub_role_menu WHERE id = ?"
        cursor.execute(query, (id,))
        conn_dsn.commit()
        cursor.close()

        return jsonify({"id": id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@menu.route("/sub-menu/<int:id>", methods=["PUT"])
@single_session_required
def sub_menu_update(id):

    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    menu_id = request.json.get("menu_id")
    sub_menu_id = request.json.get("sub_menu_id")
    title = request.json.get("title")
    icon = request.json.get("icon")
    pageName = request.json.get("pageName")

    cursor.execute("SELECT sub_menu_id FROM dbo.sub_role_menu WHERE menu_id = ? and sub_menu_id = ?", menu_id, sub_menu_id)
    existing_role = cursor.fetchone()
    if not existing_role:
        return make_response(jsonify({"msg": f'menu id "{menu_id}" dan sub menu id "{sub_menu_id}"Tidak Ada'}), 400)
    try:
        cursor = conn_dsn.cursor()
        query = "UPDATE DBO.sub_role_menu SET sub_menu_name = ?, icon = ?, redirect_to = ? WHERE id = ?"
        cursor.execute(query, (title, icon, pageName, id))
        conn_dsn.commit()
        cursor.close()

        return jsonify({"id": id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@menu.route("/sub-menu/dropdown", methods=["GET"])
@single_session_required
def menu_id_dropdown():
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401
    conn_dsn = conn.dsn()
    query_form = (
        f"""  select menu_id, menu_name from dbo.role_menu order by menu_id""")
    df = pd.read_sql(query_form, conn_dsn)
    result = df.to_dict(orient="records")
    return jsonify(data=result), 200

@menu.route("/sub-sub-menu/dropdown", methods=["GET"])
@single_session_required
def sub_id_dropdown():
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401
    conn_dsn = conn.dsn()
    query_form = (
        f""" select distinct a.sub_menu_id, b.sub_menu_name from dbo.sub_sub_role_menu a
                inner join dbo.sub_role_menu b on a.sub_menu_id = b.sub_menu_id
                order by a.sub_menu_id, b.sub_menu_name """)
    df = pd.read_sql(query_form, conn_dsn)
    result = df.to_dict(orient="records")
    return jsonify(data=result), 200

@menu.route("/sub-menu", methods=["POST"])
@single_session_required
def sub_menu_add():

    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    menu_id = request.json.get("menu_id")
    sub_menu_id = request.json.get("sub_menu_id")
    title = request.json.get("title")
    icon = request.json.get("icon")
    pageName = request.json.get("pageName")

    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()

    cursor.execute("SELECT sub_menu_id FROM dbo.sub_role_menu WHERE menu_id = ? and sub_menu_id = ? ", menu_id, sub_menu_id)
    existing_user = cursor.fetchone()
    if existing_user:
        return make_response(jsonify({"msg": f'Sub Menu "{sub_menu_id}" already exists'}), 400)

    cursor.execute("""
        INSERT INTO dbo.sub_role_menu (
           menu_id, sub_menu_id, sub_menu_name, icon, redirect_to
        ) VALUES (?, ?, ?, ?, ?)
    """,
    menu_id, sub_menu_id, title, icon, pageName)

    conn_dsn.commit()
    return make_response(jsonify({"msg": "Role Menu created successfully"}), 201)


# Parameter Sub sub Menu
@menu.route("/sub-sub-menu", methods=["GET"])
@single_session_required
def sub_sub_menu():
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401
    conn_dsn = conn.dsn()

    query = f""" select 
                    id,
                    sub_menu_id, 
                    sub_sub_menu_id,
                    sub_sub_menu_name as title, icon, 
                    redirect_to as "pageName"
                 from
	                dbo.sub_sub_role_menu order by sub_menu_id"""

    df = pd.read_sql(query, conn_dsn)
    result = df.to_dict(orient="records")
    return jsonify(result), 200

@menu.route("/sub-sub-menu/<int:id>", methods=["DELETE"])
@single_session_required
def sub_sub_menu_delete(id):
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    conn_dsn = conn.dsn()
    try:
        cursor = conn_dsn.cursor()
        query = "DELETE FROM dbo.sub_sub_role_menu WHERE id = ?"
        cursor.execute(query, (id,))
        conn_dsn.commit()
        cursor.close()

        return jsonify({"id": id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@menu.route("/sub_sub-menu/<int:id>", methods=["GET"])
@single_session_required
def sub_sub_menu_by_id(id):
    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    conn_dsn = conn.dsn()
    query = """
        SELECT 
            id,
            sub_menu_id, 
            sub_sub_menu_id,
            sub_sub_menu_name as title, icon, 
            redirect_to as "pageName"
        FROM dbo.sub_sub_role_menu
        WHERE id = ?
    """
    df = pd.read_sql(query, conn_dsn, params=[id])
    result = df.to_dict(orient="records")
    return jsonify(result), 200

@menu.route("/sub-sub-menu/<int:id>", methods=["PUT"])
@single_session_required
def sub_sub_menu_update(id):

    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()
    sub_menu_id = request.json.get("sub_menu_id")
    sub_sub_menu_id = request.json.get("sub_sub_menu_id")
    title = request.json.get("title")
    icon = request.json.get("icon")
    pageName = request.json.get("pageName")

    cursor.execute("SELECT sub_sub_menu_id FROM dbo.sub_sub_role_menu WHERE sub_menu_id = ? and sub_sub_menu_id = ?", sub_menu_id, sub_sub_menu_id)
    existing_role = cursor.fetchone()
    if not existing_role:
        return make_response(jsonify({"msg": f'sub menu id "{sub_menu_id}" dan sub sub menu id "{sub_sub_menu_id}"Tidak Ada'}), 400)
    try:
        cursor = conn_dsn.cursor()
        query = "UPDATE DBO.sub_sub_role_menu SET sub_sub_menu_name = ?, icon = ?, redirect_to = ? WHERE id = ?"
        cursor.execute(query, (title, icon, pageName, id))
        conn_dsn.commit()
        cursor.close()

        return jsonify({"id": id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@menu.route("/sub-sub-menu", methods=["POST"])
@single_session_required
def sub_sub_menu_add():

    valid, msg = verify_signature()
    if not valid:
        return jsonify({"msg": msg}), 401

    sub_menu_id = request.json.get("sub_menu_id")
    sub_sub_menu_id = request.json.get("sub_sub_menu_id")
    title = request.json.get("title")
    icon = request.json.get("icon")
    pageName = request.json.get("pageName")

    conn_dsn = conn.dsn()
    cursor = conn_dsn.cursor()

    cursor.execute("SELECT sub_sub_menu_id FROM dbo.sub_sub_role_menu WHERE sub_menu_id = ? and sub_sub_menu_id = ?", sub_menu_id, sub_sub_menu_id)
    existing_user = cursor.fetchone()
    if existing_user:
        return make_response(jsonify({"msg": f'Sub Sub Menu  "{sub_sub_menu_id}" already exists'}), 400)

    cursor.execute("""
        INSERT INTO dbo.sub_sub_role_menu (
           sub_sub_menu_id, sub_sub_menu_name, icon, redirect_to, sub_menu_id
        ) VALUES (?, ?, ?, ?, ?)
    """,
    sub_sub_menu_id, title, icon, pageName,   sub_menu_id)

    conn_dsn.commit()
    return make_response(jsonify({"msg": "Role Menu created successfully"}), 201)


