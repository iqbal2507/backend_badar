import requests
import re
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

def format_number(n):
    if n is None:
        return "N/A"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:,}"


def extract_video_id(url):
    patterns = [
        r'/video/(\d+)',
        r'@[\w.]+/video/(\d+)',
        r'v/(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def compute_engagement(data):
    views    = data.get("views")
    likes    = data.get("likes")
    comments = data.get("comments")

    if views and likes is not None:
        rate = ((likes + (comments or 0)) / views) * 100
        if rate > 10:
            level = "VIRAL - Sangat Tinggi"
        elif rate > 5:
            level = "BAGUS - Di Atas Rata-rata"
        elif rate > 2:
            level = "NORMAL - Rata-rata"
        else:
            level = "RENDAH - Di Bawah Rata-rata"
        return round(rate, 2), level
    return None, None

def method_oembed(url):
    oembed_url = "https://www.tiktok.com/oembed"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(oembed_url, params={"url": url}, headers=headers, timeout=10)
        resp.raise_for_status()
        d = resp.json()
        return {
            "source": "oembed",
            "author": d.get("author_name"),
            "author_url": d.get("author_url"),
            "title": d.get("title"),
            "thumbnail": d.get("thumbnail_url"),
            "width": d.get("thumbnail_width"),
            "height": d.get("thumbnail_height"),
            "views": None,
            "likes": None,
            "comments": None,
            "shares": None,
        }
    except Exception as e:
        return {"error": str(e)}


def method_ytdlp(url):
    try:
        import yt_dlp
    except ImportError:
        return {"error": "yt-dlp not installed. Run: pip install yt-dlp"}

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                tags = info.get("tags", [])
                hashtags = (
                    [t.get("tag") for t in tags if isinstance(t, dict)]
                    if tags and isinstance(tags[0], dict)
                    else tags
                )
                return {
                    "source": "Tiktok",
                    "author": info.get("uploader") or info.get("channel"),
                    "author_id": info.get("uploader_id"),
                    "title": info.get("title") or (info.get("description", "")[:100]),
                    "description": info.get("description", ""),
                    "duration": info.get("duration"),
                    "upload_date": info.get("upload_date"),
                    "thumbnail": info.get("thumbnail"),
                    "views": info.get("view_count"),
                    "likes": info.get("like_count"),
                    "comments": info.get("comment_count"),
                    "shares": info.get("repost_count"),
                    "hashtags": hashtags,
                }
    except Exception as e:
        return {"error": str(e)}


def method_playwright(url):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"error": "Playwright not installed. Run: pip install playwright && playwright install chromium"}

    stats_data = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 720},
                locale="en-US",
            )
            page = context.new_page()

            def handle_response(response):
                if "api/item/detail" in response.url or "api16" in response.url:
                    try:
                        body = response.json()
                        if "itemInfo" in body:
                            item  = body["itemInfo"]["itemStruct"]
                            stats = item.get("stats", {})
                            stats_data.update({
                                "views":       stats.get("playCount"),
                                "likes":       stats.get("diggCount"),
                                "comments":    stats.get("commentCount"),
                                "shares":      stats.get("shareCount"),
                                "author":      item.get("author", {}).get("uniqueId"),
                                "description": item.get("desc", ""),
                            })
                    except Exception:
                        pass

            page.on("response", handle_response)
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

            if not stats_data.get("views"):
                html        = page.content()
                stats_match = re.search(
                    r'"stats":\s*\{[^}]*"diggCount"\s*:\s*(\d+)[^}]*"shareCount"\s*:\s*(\d+)'
                    r'[^}]*"commentCount"\s*:\s*(\d+)[^}]*"playCount"\s*:\s*(\d+)',
                    html,
                )
                if stats_match:
                    stats_data = {
                        "likes":    int(stats_match.group(1)),
                        "shares":   int(stats_match.group(2)),
                        "comments": int(stats_match.group(3)),
                        "views":    int(stats_match.group(4)),
                    }

            browser.close()

            if stats_data:
                return {"source": "playwright", **stats_data}
            return {"error": "Could not extract data from page"}

    except Exception as e:
        return {"error": str(e)}


def scrape(url, method="auto"):
    data = None

    if method == "auto":
        data = method_ytdlp(url)
        print(data)
        if not data or data.get("error") or not data.get("views"):
            oembed = method_oembed(url)
            if not oembed.get("error"):
                if data and not data.get("error"):
                    data["author"]    = data.get("author") or oembed.get("author")
                    data["thumbnail"] = data.get("thumbnail") or oembed.get("thumbnail")
                else:
                    data = oembed
    elif method == "oembed":
        data = method_oembed(url)
    elif method == "ytdlp":
        data = method_ytdlp(url)
    elif method == "playwright":
        data = method_playwright(url)
    else:
        return None, "Invalid method"

    return data, None


def require_url(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        url = (request.args.get("url") or (request.get_json(silent=True) or {}).get("url", "")).strip()
        if not url:
            return jsonify({"success": False, "error": "Missing required parameter: url"}), 400
        return f(url, *args, **kwargs)
    return wrapper

@app.get("/tiktok/stats")
@require_url
def get_stats(url):
    method   = request.args.get("method", "auto").lower()
    valid    = {"auto", "ytdlp", "playwright", "oembed"}
    if method not in valid:
        return jsonify({"success": False, "error": f"Invalid method. Choose from: {', '.join(valid)}"}), 400

    video_id = extract_video_id(url)
    data, err = scrape(url, method)

    if err:
        return jsonify({"success": False, "error": err}), 400

    if not data or data.get("error"):
        return jsonify({
            "success": False,
            "error":   data.get("error") if data else "Failed to fetch data",
            "url":     url,
            "video_id": video_id,
        }), 502

    engagement_rate, engagement_level = compute_engagement(data)

    response = {
        "success":   True,
        "video_id":  video_id,
        "url":       url,
        "source":    data.get("source"),
        "author": {
            "username": data.get("author"),
            "author_id": data.get("author_id"),
            "author_url": data.get("author_url"),
        },
        "content": {
            "title":       data.get("title"),
            "description": data.get("description"),
            "upload_date": data.get("upload_date"),
        },
        "stats": {
            "views":    data.get("views"),
            "likes":    data.get("likes"),
            "comments": data.get("comments"),
            "shares":   data.get("shares"),
            "Mentions and tags": data.get("Mentions and tags"),
            "Followers": data.get("Followers"),
            "formatted": {
                "views":    format_number(data.get("views")),
                "likes":    format_number(data.get("likes")),
                "comments": format_number(data.get("comments")),
                "shares":   format_number(data.get("shares")),
                "Mentions and tags": format_number(data.get("Mentions and tags")),
                "Followers": format_number(data.get("Followers")),
            },
        },
        "engagement": {
            "rate":  engagement_rate,
            "level": engagement_level,
        },
    }

    return jsonify(response)

@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"success": False, "error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5008, use_reloader=False)
