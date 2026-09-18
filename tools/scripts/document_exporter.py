#!/usr/bin/env python3
"""
Groundsole Document Exporter
Generates professional PDFs and Microsoft Word (.docx) documents from Markdown.
- PDF: Uses the pre-installed headless browser (Edge on Windows, Chrome on Mac/Linux) for zero-dependency, pixel-perfect A4 rendering.
- Word (.docx): Uses python-docx to generate formatted Word documents.
"""

import os
import sys
import re
import subprocess
import tempfile
import argparse
from pathlib import Path

# Elegant default CSS for A4 print-ready PDFs
DEFAULT_CSS = """
@page {
    size: A4;
    margin: 20mm 20mm 20mm 20mm;
    @bottom-right {
        content: counter(page);
        font-size: 9pt;
        color: #888;
    }
}
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1a1a1a;
    background: #fff;
    margin: 0;
    padding: 0;
}
h1, h2, h3, h4 {
    color: #0f172a;
    font-weight: 700;
    page-break-after: avoid;
}
h1 {
    font-size: 22pt;
    border-bottom: 2px solid #0f172a;
    padding-bottom: 6px;
    margin-top: 0;
    margin-bottom: 16px;
}
h2 {
    font-size: 15pt;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 4px;
    margin-top: 20px;
    margin-bottom: 12px;
}
h3 {
    font-size: 12pt;
    margin-top: 16px;
    margin-bottom: 8px;
}
p {
    margin-top: 0;
    margin-bottom: 10px;
}
ul, ol {
    margin-top: 0;
    margin-bottom: 10px;
    padding-left: 24px;
}
li {
    margin-bottom: 4px;
}
blockquote {
    border-left: 4px solid #3b82f6;
    margin: 12px 0;
    padding: 8px 16px;
    background-color: #f8fafc;
    color: #334155;
}
code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
    font-size: 9.5pt;
    background-color: #f1f5f9;
    padding: 2px 4px;
    border-radius: 4px;
}
pre {
    background-color: #0f172a;
    color: #f8fafc;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 9.5pt;
    page-break-inside: avoid;
}
pre code {
    background-color: transparent;
    color: inherit;
    padding: 0;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    page-break-inside: avoid;
}
th, td {
    border: 1px solid #cbd5e1;
    padding: 8px 12px;
    text-align: left;
    font-size: 10pt;
}
th {
    background-color: #f1f5f9;
    font-weight: 600;
}
"""

def simple_markdown_to_html(md_text: str) -> str:
    """Converts basic markdown to HTML without external dependencies."""
    html_lines = []
    in_code_block = False
    in_list = False

    for line in md_text.splitlines():
        if line.strip().startswith("```"):
            if in_code_block:
                html_lines.append("</code></pre>")
                in_code_block = False
            else:
                html_lines.append("<pre><code>")
                in_code_block = True
            continue

        if in_code_block:
            escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_lines.append(escaped)
            continue

        stripped = line.strip()
        if not stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue

        # Headings
        if stripped.startswith("# "):
            html_lines.append(f"<h1>{stripped[2:].strip()}</h1>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{stripped[3:].strip()}</h2>")
        elif stripped.startswith("### "):
            html_lines.append(f"<h3>{stripped[4:].strip()}</h3>")
        elif stripped.startswith("#### "):
            html_lines.append(f"<h4>{stripped[5:].strip()}</h4>")
        # List items
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            item_content = stripped[2:].strip()
            # inline formatting
            item_content = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", item_content)
            item_content = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", item_content)
            item_content = re.sub(r"`([^`]+)`", r"<code>\1</code>", item_content)
            html_lines.append(f"<li>{item_content}</li>")
        # Blockquotes
        elif stripped.startswith("> "):
            html_lines.append(f"<blockquote>{stripped[2:].strip()}</blockquote>")
        # Regular paragraph
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            p_content = stripped
            p_content = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", p_content)
            p_content = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", p_content)
            p_content = re.sub(r"`([^`]+)`", r"<code>\1</code>", p_content)
            html_lines.append(f"<p>{p_content}</p>")

    if in_list:
        html_lines.append("</ul>")
    if in_code_block:
        html_lines.append("</code></pre>")

    body = "\n".join(html_lines)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{DEFAULT_CSS}
</style>
</head>
<body>
{body}
</body>
</html>
"""

def find_browser_executable() -> str:
    """Finds Google Chrome, Chromium, or Microsoft Edge for headless PDF printing."""
    # Windows paths (Edge is standard on 100% of Windows systems)
    windows_candidates = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    # macOS paths
    mac_candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    # Linux paths
    linux_candidates = [
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/microsoft-edge",
    ]

    all_candidates = windows_candidates + mac_candidates + linux_candidates
    for path in all_candidates:
        if os.path.exists(path):
            return path
    return ""

def export_to_pdf(input_file: Path, output_file: Path) -> bool:
    """Converts Markdown or HTML to PDF via headless browser printing."""
    browser_exe = find_browser_executable()
    if not browser_exe:
        print("❌ Kein Browser (Chrome / Edge) für PDF-Druck gefunden.")
        return False

    with open(input_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    if input_file.suffix.lower() in [".md", ".markdown"]:
        html_content = simple_markdown_to_html(raw_text)
    else:
        html_content = raw_text

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as temp_html:
        temp_html.write(html_content)
        temp_html_path = temp_html.name

    user_data_tmp = tempfile.mkdtemp(prefix="browser_pdf_")
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            browser_exe,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--user-data-dir={user_data_tmp}",
            f"--print-to-pdf={str(output_file.resolve())}",
            f"file://{temp_html_path}"
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        if output_file.exists() and output_file.stat().st_size > 0:
            print(f"✅ PDF erfolgreich erstellt: {output_file}")
            return True
        else:
            print(f"⚠️ PDF-Erstellung fehlgeschlagen: {res.stderr.decode('utf-8', errors='ignore')}")
            return False
    finally:
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        if os.path.exists(user_data_tmp):
            import shutil
            shutil.rmtree(user_data_tmp, ignore_errors=True)

def export_to_docx(input_file: Path, output_file: Path) -> bool:
    """Converts Markdown to Word (.docx) using python-docx."""
    try:
        import docx
        from docx.shared import Pt, Inches, RGBColor
    except ImportError:
        print("❌ python-docx ist nicht installiert.")
        print("👉 Installation im Terminal: pip install python-docx")
        return False

    doc = docx.Document()

    # Set standard 1-inch margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("# "):
            doc.add_heading(stripped[2:].strip(), level=1)
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:].strip(), level=2)
        elif stripped.startswith("### "):
            doc.add_heading(stripped[4:].strip(), level=3)
        elif stripped.startswith("#### "):
            doc.add_heading(stripped[5:].strip(), level=4)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            doc.add_paragraph(stripped[2:].strip(), style="List Bullet")
        else:
            doc.add_paragraph(stripped)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_file.resolve()))
    print(f"✅ Word-Dokument erfolgreich erstellt: {output_file}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Groundsole Dokumenten-Export (PDF & Word)")
    parser.add_argument("format", choices=["pdf", "docx"], help="Zielformat (pdf oder docx)")
    parser.add_argument("input", help="Pfad zur Markdown- oder HTML-Datei")
    parser.add_argument("output", nargs="?", help="Pfad zur Zieldatei (optional)")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"❌ Eingabedatei nicht gefunden: {input_path}")
        sys.exit(1)

    if args.output:
        output_path = Path(args.output).resolve()
    else:
        output_path = input_path.with_suffix(f".{args.format}")

    if args.format == "pdf":
        success = export_to_pdf(input_path, output_path)
    else:
        success = export_to_docx(input_path, output_path)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
