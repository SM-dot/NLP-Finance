"""Converts SUMMARY.md to a styled PDF via markdown -> HTML -> headless Chrome print."""
import subprocess
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
md_text = (ROOT / "SUMMARY.md").read_text(encoding="utf-8")

html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

CSS = """
@page { size: Letter; margin: 0.85in; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 11pt;
       line-height: 1.5; color: #1a1a1a; max-width: 100%; }
h1 { font-size: 19pt; margin-bottom: 4px; }
h2 { font-size: 13.5pt; margin-top: 22px; border-bottom: 1.5px solid #ccc; padding-bottom: 3px; }
h3 { font-size: 11.5pt; margin-top: 16px; }
p { margin: 8px 0; }
ul, ol { margin: 6px 0 10px 0; }
li { margin: 3px 0; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 16px 0; font-size: 9.5pt; }
th, td { border: 1px solid #bbb; padding: 4px 7px; text-align: left; }
th { background: #f0f0f0; }
img { max-width: 100%; margin: 10px 0; }
code { background: #f2f2f2; padding: 1px 4px; border-radius: 3px; font-size: 9.5pt; }
strong { color: #111; }
hr { border: none; border-top: 1px solid #ccc; margin: 18px 0 8px 0; }
em { color: #333; }
"""

html_doc = f"""<!doctype html><html><head><meta charset="utf-8">
<style>{CSS}</style></head><body>{html_body}</body></html>"""

html_path = ROOT / "SUMMARY.html"
html_path.write_text(html_doc, encoding="utf-8")

pdf_path = ROOT / "SUMMARY.pdf"
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([
    chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
    f"--print-to-pdf={pdf_path}", "--no-pdf-header-footer",
    str(html_path),
], check=True, capture_output=True)
print(f"Wrote {pdf_path} ({pdf_path.stat().st_size / 1024:.0f} KB)")
