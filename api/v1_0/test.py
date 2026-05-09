from flask import Flask, request
import requests

app = Flask(__name__)

# =========================
# CONFIG (sebaiknya pindah ke ENV kalau production)
# =========================
CLIENT_ID = "sbaw2q1plw4asxahp8"
CLIENT_SECRET = "qsQOyAjNKeCEelKxDX2Pi7tBZkgQgxMc"

REDIRECT_URI = "https://amicably-september-ambiguity.ngrok-free.dev/callback"

# =========================
# LOGIN URL
# =========================
LOGIN_URL = (
    f"https://www.tiktok.com/v2/auth/authorize/"
    f"?client_key={CLIENT_ID}"
    f"&scope=user.info.basic,video.list"
    f"&response_type=code"
    f"&redirect_uri={REDIRECT_URI}"
    f"&state=test"
)

print("\n=== BUKA URL INI DI BROWSER ===\n")
print(LOGIN_URL)


# =========================
# CALLBACK
# =========================
@app.route("/callback")
def callback():

    auth_code = request.args.get("code")
    print("\nAUTH CODE:", auth_code)

    # =========================
    # 1. GET ACCESS TOKEN
    # =========================
    token_url = "https://open.tiktokapis.com/v2/oauth/token/"

    payload = {
        "client_key": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    token_res = requests.post(token_url, data=payload, headers=headers)

    print("\n=== TOKEN RESPONSE ===")
    print(token_res.text)

    token_data = token_res.json()
    access_token = token_data.get("access_token")

    if not access_token:
        return "Gagal dapat access token"

    user_headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # =========================
    # 2. GET USER INFO
    # =========================
    user_url = "https://open.tiktokapis.com/v2/user/info/"

    user_params = {
        "fields": "open_id,display_name,avatar_url"
    }

    user_res = requests.get(user_url, headers=user_headers, params=user_params)

    print("\n=== USER INFO ===")
    print(user_res.text)

    # =========================
    # 3. GET VIDEO LIST
    # =========================
    video_url = "https://open.tiktokapis.com/v2/video/list/"

    video_params = {
        "fields": "id,title,like_count,comment_count,view_count,share_count"
    }

    video_res = requests.get(video_url, headers=user_headers, params=video_params)

    print("\n=== VIDEO LIST ===")
    print(video_res.text)

    return "SUCCESS! CEK TERMINAL"


# =========================
# RUN FLASK
# =========================
if __name__ == "__main__":
    app.run(port=5001, debug=True)