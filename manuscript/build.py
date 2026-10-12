"""Build the Technology in Society submission set from single-source templates.

review.md is a template: every {{ expression }} is replaced by a number from ../review/analysis/results.json or
figures/counts.json, and {{ include('file') }} inserts a generated table, so no number in the paper is typed by hand.
Technology in Society (Elsevier) uses double-anonymized review and APA 7th-edition references, so the build writes:
  ../output/TiS_manuscript_anonymized_<version>.docx and .pdf   (review.md: no author details)
  ../output/TiS_title_page_<version>.docx and .pdf              (title_page.md: authors, affiliations, declarations)
  ../output/TiS_highlights_<version>.docx                       (highlights.md: 3-5 bullets, <= 85 characters)
and checks the journal rules (abstract <= 250 words, 1-7 keywords, highlights, no identifying text) on every build.
Usage (from paper/manuscript):  python3 build.py [--version v1.1]"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile

import pypandoc

os.chdir(os.path.dirname(os.path.abspath(__file__)))
ver = sys.argv[sys.argv.index("--version") + 1] if "--version" in sys.argv else "v1.1"
out_dir = os.path.abspath("../output")
os.makedirs(out_dir, exist_ok=True)
os.makedirs("build", exist_ok=True)
pandoc, py = pypandoc.get_pandoc_path(), sys.executable

# ---------------------------------------------------------------- regenerate figure 1 and the tables, then render
subprocess.run([py, "figures/make_prisma.py"], check=True)
subprocess.run([py, "make_tables.py"], check=True)
if not os.path.exists("reference.docx"):
    subprocess.run([py, "make_reference_docx.py"], check=True)

R = json.load(open("../review/analysis/results.json"))
C = json.load(open("figures/counts.json"))


def _get(d, path):
    """Walk nested keys separated by '>'; a key may itself contain '>' (longest matching key wins)."""
    while path:
        k = max((k for k in d if path == k or path.startswith(k + ">")), key=len)
        d, path = d[k], path[len(k) + 1:]
    return d


v = lambda p: _get(R, p)
c = lambda p: _get(C, p)
f1 = lambda x: f"{x:.1f}"
f2 = lambda x: f"{x:.2f}".replace("-", "−")
f3 = lambda x: f"{x:.3f}"
n = lambda x: f"{x:,}"
pc = lambda x: f"{round(100 * x)}".replace("-", "−")
pc_of = lambda a, b: f"{round(100 * a / b)}"
med = lambda p: f2(v(p)["median"])
iqr = lambda p: f"{f2(v(p)['q1'])}–{f2(v(p)['q3'])}"
ci = lambda p: f"{f2(v(p)['ci_lo'])}–{f2(v(p)['ci_hi'])}"
n_ = lambda p: v(p)["n"]
ch = lambda group, key: R["characteristics"][group].get(key, 0)
a = lambda q, level: R["appraisal"][q][level]
ap = lambda q, level: pc_of(R["appraisal"][q][level], R["n_appraised"])
wc = lambda name, field: R["within_study_contrasts"][name][field]
tx = lambda task, shift: f2(R["ret_by_task_shift"][f"{task}|{shift}"]["median"])
include = lambda path: open(path).read().strip()
NS = dict(v=v, c=c, f1=f1, f2=f2, f3=f3, n=n, pc=pc, pc_of=pc_of, med=med, iqr=iqr, ci=ci, n_=n_, ch=ch, a=a, ap=ap,
          wc=wc, tx=tx, include=include)


def render(text):
    return re.sub(r"\{\{(.+?)\}\}", lambda m: str(eval(m.group(1), {"__builtins__": {}}, NS)), text, flags=re.S)


def render_file(path, out):
    text = render(open(path, encoding="utf-8").read())
    if "{{" in text:                      # LaTeX can contain "}}" but never "{{"
        sys.exit(f"unrendered template markers remain in {path}: " +
                 " | ".join(m.group(0) for m in re.finditer(r".{0,40}\{\{.{0,40}", text)))
    out = os.path.abspath(out)
    open(out, "w", encoding="utf-8").write(text)
    return out, text


src, rendered = render_file("review.md", "build/review_rendered.md")
tp_src, tp_text = render_file("title_page.md", "build/title_page_rendered.md")
hl_src, hl_text = render_file("highlights.md", "build/highlights_rendered.md")

# ---------------------------------------------------------------- Technology in Society rules, checked on every build
checks = []
front = rendered.split("\n---\n", 1)[0]
abstract = re.search(r"abstract: \|\n((?:  .*\n?)+)", front).group(1)
n_abs = len(re.findall(r"\S+", abstract))
checks.append(("abstract <= 250 words", n_abs <= 250, f"{n_abs} words"))
kw = re.search(r"\*\*Keywords:\*\*\s*(.+)", rendered).group(1)
n_kw = len([k for k in kw.split(";") if k.strip()])
checks.append(("1-7 keywords", 1 <= n_kw <= 7, f"{n_kw} keywords"))
bullets = [b[2:].strip() for b in hl_text.splitlines() if b.startswith("- ")]
long_ = [f"{len(b)} chars: {b}" for b in bullets if len(b) > 85]
checks.append(("3-5 highlights, each <= 85 characters incl. spaces", 3 <= len(bullets) <= 5 and not long_,
               f"{len(bullets)} bullets, longest {max(map(len, bullets))} characters" + ("; " + "; ".join(long_) if long_ else "")))
IDENT = r"\b(Abinash|Binayak|Pant|Mishra|2abi5|usu\.edu|Utah State)\b|github\.com|location_doner"
hits = sorted({m.group(0) for m in re.finditer(IDENT, rendered, re.I)})
checks.append(("anonymized manuscript has no author-identifying text", not hits, ", ".join(hits) or "none found"))
checks.append(("highlights moved out of the manuscript", "**Highlights**" not in rendered, "separate file"))
checks.append(("AI declaration titled as Elsevier requires",
               "Declaration of generative AI and AI-assisted technologies in the writing process" in rendered, "before References"))
for name_, ok, detail in checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name_}: {detail}")
json.dump([dict(check=a, ok=b, detail=c) for a, b, c in checks], open("build/tis_checks.json", "w"), indent=1)

# ---------------------------------------------------------------- outputs
common = ["--citeproc", "--bibliography=refs.bib", "--bibliography=generated/included.bib",
          "--csl=apa.csl", "--resource-path=.:figures"]
CANDIDATES = ["/opt/pw-browsers/chromium", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              shutil.which("chromium") or "", shutil.which("google-chrome") or ""]
chrome = next((p for p in CANDIDATES if p and os.path.exists(p)), None)


def scrub_docx(path):
    """Blank the creator and last-modified-by fields so the Word file carries no identity."""
    tmp = path + ".tmp"
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "docProps/core.xml":
                xml = data.decode("utf-8")
                xml = re.sub(r"<dc:creator>.*?</dc:creator>", "<dc:creator></dc:creator>", xml, flags=re.S)
                xml = re.sub(r"<cp:lastModifiedBy>.*?</cp:lastModifiedBy>", "<cp:lastModifiedBy></cp:lastModifiedBy>", xml, flags=re.S)
                data = xml.encode("utf-8")
            zout.writestr(item, data)
    os.replace(tmp, path)


def to_docx(md, out, numbered):
    subprocess.run([pandoc, md, *common, *(["--number-sections"] if numbered else []),
                    "--reference-doc=reference.docx", "-o", out], check=True)
    scrub_docx(out)
    with zipfile.ZipFile(out) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    print("docx:", out, "| line numbers:", "lnNumType" in xml)


def to_pdf(md, out, title, numbered):
    if chrome is None:
        sys.exit("no Chrome or Chromium found for PDF printing")
    html = os.path.abspath(f"build/{os.path.basename(out)[:-4]}.html")
    subprocess.run([pandoc, md, *common, *(["--number-sections"] if numbered else []), "-s", "--embed-resources",
                    "--css=pdf.css", "--lua-filter=svg.lua", "--mathml", f"--metadata=pagetitle:{title}", "-o", html],
                   check=True)
    if os.path.exists(out):
        os.remove(out)
    profile = os.path.abspath("build/chrome-profile")
    proc = subprocess.Popen([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-first-run",
                             "--disable-extensions", "--no-pdf-header-footer", f"--user-data-dir={profile}",
                             f"--print-to-pdf={out}", "file://" + html],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    last, stable = -1, 0
    for _ in range(240):                  # Chrome writes the PDF, then may linger; stop it once the file is stable
        time.sleep(1)
        size = os.path.getsize(out) if os.path.exists(out) else -1
        stable = stable + 1 if size > 0 and size == last else 0
        last = size
        if stable >= 3 or proc.poll() is not None:
            break
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    subprocess.run(["pkill", "-f", profile], capture_output=True)
    print("pdf: ", out, f"({os.path.getsize(out) // 1024} KB)" if os.path.exists(out) else "(not written)")


base = f"{out_dir}/TiS"
to_docx(src, f"{base}_manuscript_anonymized_{ver}.docx", numbered=True)
to_pdf(src, f"{base}_manuscript_anonymized_{ver}.pdf", "Manuscript", numbered=True)
to_docx(tp_src, f"{base}_title_page_{ver}.docx", numbered=False)
to_pdf(tp_src, f"{base}_title_page_{ver}.pdf", "Title page", numbered=False)
to_docx(hl_src, f"{base}_highlights_{ver}.docx", numbered=False)
