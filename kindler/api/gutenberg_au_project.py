import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from flask import (
    render_template,
    Blueprint,
    request,
    redirect,
    url_for,
    send_file,
    Response,
    abort,
)
from pathvalidate import sanitize_filename

from kindler.search import FuzzySearcher

gutenberg_au_bp = Blueprint("gutenberg_au", __name__, url_prefix="/gutenberg_au")

allowed_formats = {"html", "epub", "mobi", "azw3"}

searcher = FuzzySearcher()


@gutenberg_au_bp.route("/")
def home():
    return render_template("index_gutenberg_au.html")


@gutenberg_au_bp.route("/search")
def search():
    # TODO - support multiple pages
    query = request.args.get("q")
    books = searcher.search(query)
    return render_template("result_gutenberg_au.html", query=query, results=books)


## TODO optimize pulling and rendering
@gutenberg_au_bp.route("/readability")
def readability_page():
    query = request.args.get("q")
    url = request.args.get("url")
    if not url:
        logging.warning("Readability URL is empty.")
        return redirect(url_for("error.error", status_code=400))
    try:
        try:
            head_resp = requests.head(url, allow_redirects=True, timeout=5)
            content_type = head_resp.headers.get("Content-Type", "").lower()
            if content_type and not (
                content_type.startswith("text/html")
                or content_type.startswith("application/xhtml+xml")
            ):
                return redirect(url)
        except requests.RequestException:
            logging.info(f"HEAD request failed for {url}, falling back to GET.")
        req = requests.get(url, timeout=10)
        req.raise_for_status()
        content_type = req.headers.get("Content-Type", "").lower()
        if not (
            content_type.startswith("text/html")
            or content_type.startswith("application/xhtml+xml")
        ):
            return redirect(url)
        article = get_python_readability_result(req.text, url)
        return render_template(
            "read_gutenberg_au.html",
            title=article["title"],
            query=query,
            content=article["content"],
            url=url,
        )
    except requests.exceptions.RequestException as e:
        logging.warning(f"Network error fetching URL: {e}")
        status_code = 500
        if hasattr(e, "response") and e.response is not None:
            status_code = getattr(e.response, "status_code", 500)
        return redirect(url_for("error.error", status_code=status_code))
    except Exception as e:
        logging.error(f"An error occurred during readability processing: {e}")
        return f"An error occurred during processing: {e}", 500


@gutenberg_au_bp.route("/save_page")
def save_page():
    url = request.args.get("url")
    save_format = request.args.get("format", "html")
    if not url:
        return "No URL provided", 400
    if save_format not in allowed_formats:
        abort(400, "Invalid format")
    req = requests.get(url, timeout=10)
    if "html" == save_format:
        article = get_python_readability_result(req.text, url, None)
        html_content = render_template(
            "read_save_formatted_gutenberg_au.html",
            title=article["title"],
            content=article["content"],
            url=url,
        )
        response = Response(html_content, mimetype="text/html")
        response.headers["Content-Disposition"] = (
            f"attachment; filename={sanitize_filename(article['title'] + '.html')}"
        )
        return response
    else:
        temp_dir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        os.makedirs(temp_dir, exist_ok=True)
        article = get_python_readability_result(req.text, url, img_dir=temp_dir)
        html_content = render_template(
            "read_save_formatted_gutenberg_au.html",
            title=article["title"],
            content=article["content"],
            url=url,
        )
        cover_image_path = article["cover"]
        input_html_file = os.path.join(temp_dir, "page.html")
        with open(input_html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        with tempfile.NamedTemporaryFile(
            suffix=f".{save_format}", delete=False
        ) as output_tmp:
            output_file = output_tmp.name
        try:
            cmd = [
                "ebook-convert",
                input_html_file,
                output_file,
                "--chapter",
                "//div[@style='page-break-before: always;']",
                "--chapter-mark",
                "pagebreak",
            ]
            if cover_image_path:
                cmd.extend(["--cover", cover_image_path])
            subprocess.run(
                cmd,
                check=True,
            )
            download_file_name = sanitize_filename(f"{article['title']}.{save_format}")
            response = send_file(
                output_file, as_attachment=True, download_name=download_file_name
            )

            @response.call_on_close
            def cleanup():
                for f in [input_html_file, output_file]:
                    try:
                        os.remove(f)
                        logging.info(f"File {f} deleted")
                    except OSError:
                        pass
                shutil.rmtree(temp_dir, ignore_errors=True)

            return response
        except subprocess.CalledProcessError as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if os.path.exists(output_file):
                os.remove(output_file)
            abort(500, f"Conversion failed: {e}")


def get_python_readability_result(html_content, base_url, img_dir=None):
    content, cover_image_path, title = remove_excessive_elements(
        html_content, base_url, img_dir
    )
    return {"content": content, "title": title, "cover": cover_image_path}


def remove_excessive_elements(html_content, url, img_dir):
    cover_image_path = None
    soup = BeautifulSoup(html_content, "html.parser")
    for style_tag in soup.find_all("style"):
        style_tag.decompose()
    for p in soup.find_all("p", class_="author"):
        p["style"] = "text-align: center;"
    heading = soup.find(["h1", "h2", "h3", "h4"])
    if heading:
        for elem in list(heading.previous_siblings):
            if elem.name == "img":
                continue
            elif elem.name in ["p", "a"] and elem.find("img"):
                for img in elem.find_all("img"):
                    elem.insert_after(img)
                elem.extract()
            else:
                elem.extract()
        heading["style"] = "text-align: center;"
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        h["style"] = "text-align: center;"
    for h2 in soup.find_all("h2"):
        if h2.get_text(strip=True) == "THE END":
            hr_before = h2.find_previous("hr")
            if hr_before:
                for element in list(h2.find_all_next()):
                    element.extract()
                h2.extract()
            break
    for h2 in soup.find_all("h3"):
        if h2.get_text(strip=True) == "THE END":
            for element in list(h2.find_all_next()):
                element.extract()
            h2.extract()
    for i, img in enumerate(soup.find_all("img")):
        src = img.get("src")
        if not src:
            continue
        img_url = urljoin(url, src)
        if img_dir:
            ext = os.path.splitext(img_url)[1] or ".png"
            local_filename = f"img{i}{ext}"
            local_path = os.path.join(img_dir, local_filename)
            if not cover_image_path:
                cover_image_path = local_path
            try:
                img_request = requests.get(img_url, timeout=10)
                if img_request.status_code != 200:
                    cover_image_path = None
                    img.extract()
                    continue
                img_data = img_request.content
                with open(local_path, "wb") as f:
                    f.write(img_data)
                if cover_image_path == local_path:
                    img.extract()
                else:
                    img["src"] = local_filename
            except Exception as e:
                logging.error(f"Failed to download {img_url}: {e}")
        else:
            img["src"] = img_url
    if img_dir:
        fix_by_keyword_on_ebook_generation(soup)
        for hr in soup.find_all("hr"):
            page_break_div = soup.new_tag("div", style="page-break-before: always;")
            hr.replace_with(page_break_div)
    return str(soup), cover_image_path, soup.title.string


def fix_by_keyword_on_ebook_generation(soup):
    headers = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    for i, header in enumerate(headers):
        if "by" in header.get_text(strip=True).lower():
            j = i + 1
            while j < len(headers):
                next_header = headers[j]
                if not next_header.get_text(strip=True):
                    j += 1
                    continue
                if next_header.name in ["h1", "h2"]:
                    next_header.name = "h4"
                break
            break
