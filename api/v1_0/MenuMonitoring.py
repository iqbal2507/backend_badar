# api/v1_0/MenuMonitoring.py

from flask import Blueprint, jsonify, make_response
import pandas as pd
import config.connection as conn
from flask_jwt_extended import get_jwt_identity
from api.v1_0.security import single_session_required

MenuMonitoring = Blueprint('MenuMonitoring', __name__)

# ================= GET ALL =================
@MenuMonitoring.route("", methods=["GET"])
@single_session_required
def get_MenuMonitoring():

    conn_dsn = conn.dsn()

    query = """
        SELECT
            id,
            medsos,
            tema,
            tgl_input,
            user_input,
            link,
            username,
            title,
            view,
            liked,
            comment,
            share,
            saved,
            engagement
        FROM dbo.monitoring_link
        ORDER BY id DESC
    """

    df = pd.read_sql(query, conn_dsn)

    # convert date -> string
    if 'tgl_input' in df.columns:
        df['tgl_input'] = df['tgl_input'].astype(str)

    current_user = get_jwt_identity()

    result = df.to_dict(orient="records")

    return jsonify(
        logged_in_as=current_user,
        data=result
    ), 200


# ================= GET BY ID =================
@MenuMonitoring.route("/<int:id>", methods=["GET"])
@single_session_required
def get_MenuMonitoring_by_id(id):

    conn_dsn = conn.dsn()

    query = """
        SELECT
            id,
            medsos,
            tema,
            tgl_input,
            user_input,
            link,
            username,
            title,
            view,
            liked,
            comment,
            share,
            saved,
            engagement
        FROM dbo.monitoring_link
        WHERE id = ?
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

        # convert date -> string
        if 'tgl_input' in df.columns:
            df['tgl_input'] = df['tgl_input'].astype(str)

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
@MenuMonitoring.route("/<int:id>", methods=["DELETE"])
@single_session_required
def delete_MenuMonitoring(id):

    conn_dsn = conn.dsn()

    current_user = get_jwt_identity()

    try:

        cursor = conn_dsn.cursor()

        cursor.execute(
            "DELETE FROM dbo.monitoring_link WHERE id = ?",
            (id,)
        )

        conn_dsn.commit()

        cursor.close()

        return jsonify(
            logged_in_as=current_user,
            message="Data berhasil dihapus",
            id=id
        ), 200

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500


# ================= CREATE =================
@MenuMonitoring.route("", methods=["POST"])
@single_session_required
def create_MenuMonitoring():

    try:

        conn_dsn = conn.dsn()

        current_user = get_jwt_identity()

        data = request.get_json()

        medsos = data.get("medsos")
        tema = data.get("tema")
        link = data.get("link")
        username = data.get("username")
        title = data.get("title")

        view = data.get("view", "0")
        liked = data.get("liked", "0")
        comment = data.get("comment", "0")
        share = data.get("share", "0")
        saved = data.get("saved", "0")
        engagement = data.get("engagement", "0")

        if not medsos or not link:

            return jsonify({
                "message": "medsos & link wajib diisi"
            }), 400

        query = """
            INSERT INTO dbo.monitoring_link
            (
                medsos,
                tema,
                tgl_input,
                user_input,
                link,
                username,
                title,
                view,
                liked,
                comment,
                share,
                saved,
                engagement
            )
            VALUES
            (
                ?, ?, CURRENT_DATE, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """

        with conn_dsn.cursor() as cursor:

            cursor.execute(query, (
                medsos,
                tema,
                current_user,
                link,
                username,
                title,
                view,
                liked,
                comment,
                share,
                saved,
                engagement
            ))

            conn_dsn.commit()

        return jsonify({
            "message": "Monitoring berhasil ditambahkan"
        }), 201

    except Exception as e:

        import traceback
        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500


# ================= UPDATE =================
@MenuMonitoring.route("/<int:id>", methods=["PUT"])
@single_session_required
def update_MenuMonitoring(id):

    try:

        conn_dsn = conn.dsn()

        data = request.get_json()

        medsos = data.get("medsos")
        tema = data.get("tema")
        link = data.get("link")
        username = data.get("username")
        title = data.get("title")

        view = data.get("view", "0")
        liked = data.get("liked", "0")
        comment = data.get("comment", "0")
        share = data.get("share", "0")
        saved = data.get("saved", "0")
        engagement = data.get("engagement", "0")

        query = """
            UPDATE dbo.monitoring_link
            SET
                medsos = ?,
                tema = ?,
                link = ?,
                username = ?,
                title = ?,
                view = ?,
                liked = ?,
                comment = ?,
                share = ?,
                saved = ?,
                engagement = ?
            WHERE id = ?
        """

        with conn_dsn.cursor() as cursor:

            cursor.execute(query, (
                medsos,
                tema,
                link,
                username,
                title,
                view,
                liked,
                comment,
                share,
                saved,
                engagement,
                id
            ))

            conn_dsn.commit()

        return jsonify({
            "message": "Monitoring berhasil diupdate"
        }), 200

    except Exception as e:

        import traceback
        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500