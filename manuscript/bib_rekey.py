"""Give refs.bib entries readable keys: surname + year + first content word of the title."""
import re, unicodedata
STOP = {"a", "an", "the", "on", "of", "in", "for", "and", "to", "from", "with", "using", "towards", "toward", "is", "are"}
src = open("refs.bib").read()

def field(entry, name):
    m = re.search(r"[,\s]" + name + r"\s*=\s*\{", entry, re.I)
    if not m:
        return ""
    i, depth, out = m.end(), 1, []
    while i < len(entry) and depth:
        c = entry[i]; depth += (c == "{") - (c == "}")
        if depth: out.append(c)
        i += 1
    return "".join(out)

def ascii(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()

entries = re.split(r"\n(?=@)", src.strip())
used, out = set(), []
for e in entries:
    people = field(e, "author") or field(e, "editor") or "anon"
    first = ascii(people.split(" and ")[0]).strip()
    last = first.split(",")[0] if "," in first else first.split()[-1]
    last = re.sub(r"[^a-z]", "", last.lower())
    year = (re.search(r"\d{4}", field(e, "year")) or re.search(r"\d{4}", "0000")).group(0)
    words = [w for w in re.findall(r"[a-z0-9]+", ascii(field(e, "title")).lower()) if w not in STOP]
    key = f"{last}{year}{words[0] if words else ''}"
    base, n = key, 1
    while key in used:
        n += 1; key = f"{base}{chr(96 + n)}"
    used.add(key)
    out.append(re.sub(r"^@(\w+)\{[^,]*,", lambda m: f"@{m.group(1)}{{{key},", e, count=1))
open("refs.bib", "w").write("\n\n".join(out) + "\n")
print(" ".join(sorted(used)))
