import re
from html import escape
from urllib.parse import urljoin


def gemtext_to_html(gemtext: str) -> dict:
    html_lines = []
    in_list = False
    title = None

    for line in gemtext.splitlines():
        if line.startswith("### "):
            html_lines.append(f"<h3>{escape(line[4:])}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("# "):
            # Use first heading as title
            heading_text = line[2:]
            if title is None:
                title = heading_text
            html_lines.append(f"<h1>{escape(heading_text)}</h1>")
        elif line.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{escape(line[2:])}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if line.startswith('=>'):
                href, text = clean_gemini_link(line)
                if href and text:
                    html_lines.append(f'<p><a href="{href}">{text}</a></p>')

            elif line.startswith("```"):
                # NOTE: for simplicity, this just opens <pre>. A real parser should detect closing ```
                html_lines.append("<pre>")
            else:
                html_lines.append(f"<p>{escape(line)}</p>")

    if in_list:
        html_lines.append("</ul>")

    return {
        "title": title,
        "content": "\n".join(html_lines)
    }


def clean_gemini_link(line, base_url=""):
    raw = line[2:].lstrip()
    match = re.match(r"(\S+)(?:\s+(.*))?", raw)
    if not match:
        return None, None
    url = match.group(1)
    link_text = match.group(2) if match.group(2) else url
    url = re.sub(r'[\t\u21BA\u21BB\u279C➜↩↪]+$', '', url)
    if base_url:
        url = urljoin(base_url, url)
    return escape(url), escape(link_text)
