"""Build plugin/gen/fonts.css: the website board fonts (our self-hosted fonts-boards-v1.css: Hanken Grotesk, JetBrains
Mono, Bricolage Grotesque, all SIL OFL 1.1, licences in ../piquesignal/fonts/) embedded as data: URLs, so the panel
shows the website's real fonts with no network request. The families get panel-only names ("PQS ...") so they can
never change how Hermes itself draws text; gen_css.py points the board sheets at the same names (FAMILY_MAP).
Every input file is md5-checked against the pinned live copy.
Usage: py gen_fonts.py <dir with fonts-boards-v1.css + the woff2 files> <out.css>
"""
import base64
import hashlib
import re
import sys
from pathlib import Path

FAMILY_MAP = {"Hanken Grotesk": "PQS Hanken Grotesk", "JetBrains Mono": "PQS JetBrains Mono",
              "Bricolage Grotesque": "PQS Bricolage Grotesque"}
CSS_MD5 = "71d3e2f9"
WOFF2_MD5 = {   # first 8 of md5 of the pinned live copies
    "hankengrotesk-v12-ieVn2YZDLWuGJpnzaiwFXS9tYtpQ59CjCQ.woff2": "d68813c6",
    "hankengrotesk-v12-ieVn2YZDLWuGJpnzaiwFXS9tYtpS59CjCQ.woff2": "df92a194",
    "hankengrotesk-v12-ieVn2YZDLWuGJpnzaiwFXS9tYtpT59CjCQ.woff2": "20672d21",
    "hankengrotesk-v12-ieVn2YZDLWuGJpnzaiwFXS9tYtpd59A.woff2": "c501f578",
    "jetbrainsmono-v24-tDbv2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yKwBNntkaToggR7BYRbKPx3cwhsk.woff2": "3ae0dad2",
    "jetbrainsmono-v24-tDbv2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yKwBNntkaToggR7BYRbKPx7cwhsk.woff2": "bd4781a3",
    "jetbrainsmono-v24-tDbv2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yKwBNntkaToggR7BYRbKPxDcwg.woff2": "b636a65d",
    "jetbrainsmono-v24-tDbv2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yKwBNntkaToggR7BYRbKPxPcwhsk.woff2": "b1b5690e",
    "jetbrainsmono-v24-tDbv2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yKwBNntkaToggR7BYRbKPxTcwhsk.woff2": "3576e677",
    "jetbrainsmono-v24-tDbv2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yKwBNntkaToggR7BYRbKPx_cwhsk.woff2": "ffcfa7a2",
    "bricolagegrotesque-v9-3y9K6as8bTXq_nANBjzKo3IeZx8z6up5BeSl9D4dj_x9PpZBMlGGInHEVA.woff2": "c4c7bb6a",
    "bricolagegrotesque-v9-3y9K6as8bTXq_nANBjzKo3IeZx8z6up5BeSl9D4dj_x9PpZBMlGHInHEVA.woff2": "8c5bedf8",
    "bricolagegrotesque-v9-3y9K6as8bTXq_nANBjzKo3IeZx8z6up5BeSl9D4dj_x9PpZBMlGIInE.woff2": "ad33cbc6",
}
FACE_RE = re.compile(r"@font-face\s*\{([^{}]*)\}")
ALLOWED_DESCRIPTORS = {"font-family", "font-style", "font-weight", "font-stretch", "font-display", "src", "unicode-range"}


def md5_8(b):
    return hashlib.md5(b).hexdigest()[:8]


def main(src_dir, out):
    src = Path(src_dir)
    raw = (src / "fonts-boards-v1.css").read_bytes()
    if md5_8(raw) != CSS_MD5:
        raise SystemExit("STOP: fonts-boards-v1.css md5 %s != live %s (use the matching copy)" % (md5_8(raw), CSS_MD5))
    css = re.sub(r"/\*.*?\*/", "", raw.decode("utf-8"), flags=re.S)
    if re.sub(FACE_RE, "", css).strip():
        raise SystemExit("STOP: fonts-boards-v1.css has something other than @font-face rules")
    data, faces, used, faces_by_key = {}, [], set(), {}
    for m in FACE_RE.finditer(css):
        decl = {}
        for part in m.group(1).split(";"):
            if not part.strip():
                continue
            k, _, v = part.partition(":")
            k, v = k.strip(), v.strip()
            if k not in ALLOWED_DESCRIPTORS:
                raise SystemExit("STOP: unexpected @font-face descriptor %r" % k)
            decl[k] = v
        fam = decl.get("font-family", "").strip("'\"")
        if fam not in FAMILY_MAP:
            raise SystemExit("STOP: unexpected font family %r" % fam)
        um = re.fullmatch(r"url\(/static/fonts/([A-Za-z0-9_\-]+\.woff2)\) format\('woff2'\)", decl.get("src", ""))
        if not um or um.group(1) not in WOFF2_MD5:
            raise SystemExit("STOP: unexpected src %r" % decl.get("src"))
        name = um.group(1)
        if name not in data:
            b = (src / name).read_bytes()
            if md5_8(b) != WOFF2_MD5[name] or b[:4] != b"wOF2":
                raise SystemExit("STOP: %s md5 %s != live %s (or not woff2)" % (name, md5_8(b), WOFF2_MD5[name]))
            data[name] = base64.b64encode(b).decode("ascii")
        used.add(name)
        w = decl.get("font-weight", "400")
        if not re.fullmatch(r"\d{3}", w):
            raise SystemExit("STOP: unexpected font-weight %r" % w)
        # Google serves variable fonts: the same file is listed once per weight. Merge them into ONE face with a
        # weight range, so each file is embedded once (same glyphs, same rendering).
        key = (FAMILY_MAP[fam], decl.get("font-style", "normal"), decl.get("font-stretch"), decl.get("font-display"),
               name, decl.get("unicode-range"))
        if key in faces_by_key:
            faces_by_key[key].append(int(w))
        else:
            faces_by_key[key] = [int(w)]
    # Only UNBROKEN runs of declared weights are merged (400+500 -> "400 500"; a lone 700 stays "700"), so the browser
    # picks exactly the face the website picks for every weight the boards use (whole hundreds only).
    runs_out = []
    for (fam2, style, stretch, display, name, urange), weights in faces_by_key.items():
        ws = sorted(set(weights))
        run = [ws[0]]
        for w in ws[1:]:
            if w == run[-1] + 100:
                run.append(w)
            else:
                runs_out.append((fam2, style, stretch, display, name, urange, run))
                run = [w]
        runs_out.append((fam2, style, stretch, display, name, urange, run))
    for fam2, style, stretch, display, name, urange, run in runs_out:
        wr = "%d" % run[0] if len(run) == 1 else "%d %d" % (run[0], run[-1])
        parts = ["font-family:'%s'" % fam2, "font-style:%s" % style, "font-weight:%s" % wr]
        if stretch:
            parts.append("font-stretch:%s" % stretch)
        if display:
            parts.append("font-display:%s" % display)
        parts.append("src:url(data:font/woff2;base64,%s) format('woff2')" % data[name])
        if urange:
            parts.append("unicode-range:%s" % urange)
        faces.append("@font-face{" + ";".join(parts) + "}")
    if used != set(WOFF2_MD5):
        raise SystemExit("STOP: font files used %d != pinned %d" % (len(used), len(WOFF2_MD5)))
    text = "\n".join(faces) + "\n"
    if "<" in text:
        raise SystemExit("STOP: '<' in fonts.css")
    Path(out).write_text(text, encoding="utf-8", newline="\n")
    print(out, len(faces), "faces,", len(data), "files,", len(text), "chars")


if __name__ == "__main__":
    main(*sys.argv[1:3])
