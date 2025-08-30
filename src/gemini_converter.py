import html
from html import escape


def escape(text: str) -> str:
    """A helper function to escape HTML characters in text."""
    return html.escape(text)


def gemtext_to_html(gemtext: str) -> dict:
    """
    Converts a Gemtext string into a dictionary containing HTML content and a title.

    This enhanced version correctly handles code blocks, links, and blockquotes,
    providing a more robust conversion.

    Args:
        gemtext: The input Gemtext content as a string.

    Returns:
        A dictionary with "title" and "content" keys, where content is an
        HTML string.
    """
    html_lines = []
    in_list = False
    in_code_block = False
    title = None

    lines = gemtext.splitlines()
    for i, line in enumerate(lines):
        # Handle code blocks
        if line.startswith("```"):
            if not in_code_block:
                html_lines.append("<code><pre>")
                in_code_block = True
            else:
                html_lines.append("</pre></code>")
                in_code_block = False
            continue

        if in_code_block:
            html_lines.append(escape(line))
            continue

        # Handle lists
        if line.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{escape(line[2:])}</li>")
            continue
        elif in_list:
            html_lines.append("</ul>")
            in_list = False

        # Handle headings
        if line.startswith("### "):
            html_lines.append(f"<h3>{escape(line[4:])}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("# "):
            heading_text = line[2:]
            if title is None:
                title = heading_text
            html_lines.append(f"<h1>{escape(heading_text)}</h1>")
        # Handle links
        elif line.startswith('=>'):
            parts = line[2:].strip().split(maxsplit=1)
            href = parts[0]
            link_text = parts[1] if len(parts) > 1 else href
            html_lines.append(f'<p><a href="{href}">{escape(link_text)}</a></p>')
        # Handle blockquotes
        elif line.startswith(">"):
            html_lines.append(f"<blockquote>{escape(line[1:].strip())}</blockquote>")
        # Handle regular paragraphs
        else:
            if line:
                html_lines.append(f"<p>{escape(line)}</p>")

    # Close any open list or code block at the end of the file
    if in_list:
        html_lines.append("</ul>")
    if in_code_block:
        html_lines.append("</code></pre>")

    return {
        "title": title,
        "content": "\n".join(html_lines)
    }
