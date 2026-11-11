"""Generate the panel's CSS from the LIVE-AFTER-GO-LIVE website board pages, so the Hermes screens look identical.

For each page: take every <style> block in document order (minus the website's 'desktop-only' guard), strip comments,
and rewrite it so it applies ONLY inside our root element:
  * every selector is prefixed with the root (html / body / :root map onto the root itself); ids stay as they are
    (the board scripts look them up, always inside our root, so a same-named Hermes id is never matched);
  * @media width rules (min/max-width) become @container rules on the panel's own width (the pane / page is the
    "screen"); touch/hover/device rules are fixed per variant (phone = touch, desktop = mouse); print rules are dropped;
    prefers-reduced-motion stays a real media query;
  * @keyframes names get a 'pqs-' prefix (and every animation reference follows), so nothing clashes with Hermes;
  * 'vw' lengths become 'cqw' (the panel's width, not the Hermes window's).
Usage: py gen_css.py <page.html> <phone|desktop> <root selector> <out.css>
"""
import re
import sys

KEEP_MEDIA = re.compile(r"^\(prefers-reduced-motion:\s*reduce\)$")


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def parse(css):
    """Top-level CSS -> list of (prelude, body or None for statements). body is raw text inside the braces."""
    out, i, n = [], 0, len(css)
    while i < n:
        j = i
        while j < n and css[j] not in "{;}":
            if css[j] in "\"'":
                q = css[j]; j += 1
                while j < n and css[j] != q:
                    j += 2 if css[j] == "\\" else 1
            j += 1
        if j >= n:
            break
        if css[j] == ";":
            out.append((css[i:j].strip(), None)); i = j + 1; continue
        if css[j] == "}":
            i = j + 1; continue
        pre = css[i:j].strip(); d = 0; k = j
        while k < n:
            c = css[k]
            if c in "\"'":
                q = c; k += 1
                while k < n and css[k] != q:
                    k += 2 if css[k] == "\\" else 1
            elif c == "{":
                d += 1
            elif c == "}":
                d -= 1
                if d == 0:
                    break
            k += 1
        out.append((pre, css[j + 1:k])); i = k + 1
    return out


def split_top(s, sep=","):
    parts, d, cur, q = [], 0, "", None
    for c in s:
        if q:
            cur += c
            if c == q:
                q = None
            continue
        if c in "\"'":
            q = c
        elif c in "([":
            d += 1
        elif c in ")]":
            d -= 1
        if c == sep and d == 0:
            parts.append(cur); cur = ""
        else:
            cur += c
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


_LEAD = re.compile(r"^(html|:root|body)(?=$|[\s.:\[#>~+])")


def scope_selector(sel, root):
    sel = sel.strip()   # ids stay real: the board scripts look them up (always inside our root)
    attached = ""
    rest = sel
    for _ in range(2):                       # html / :root, then body
        m = _LEAD.match(rest)
        if not m:
            break
        rest = rest[m.end():]
        suf = re.match(r"^([.:\[][^\s>~+]*)", rest)
        if suf:
            attached += suf.group(1); rest = rest[suf.end():]
        rest = rest.lstrip()
    if attached or rest != sel:
        return (root + attached + (" " + rest if rest else "")).strip()
    if sel == "*" or sel.startswith("*"):
        return root + " " + sel
    return root + " " + sel


def eval_feature(f, phone):
    """-> ('static', bool) | ('container', text) | ('media', text)"""
    g = re.sub(r"\s+", "", f.lower())
    if KEEP_MEDIA.match(g):
        return ("media", f)
    if g in ("(pointer:coarse)", "(any-pointer:coarse)", "(any-hover:none)", "(hover:none)"):
        return ("static", phone)
    if g in ("(pointer:fine)", "(any-pointer:fine)", "(hover:hover)", "(any-hover:hover)"):
        return ("static", not phone)
    if re.match(r"^\(max-device-(width|height):\d+(\.\d+)?px\)$", g):
        return ("static", phone)
    if re.match(r"^\((min|max)-width:\d+(\.\d+)?px\)$", g):
        return ("container", f)
    if g in ("screen", "all"):
        return ("static", True)
    if g == "print":
        return ("static", False)
    raise ValueError("unknown media feature: " + f)


def eval_query(q, phone):
    """One media query (no commas) -> None (never true) | (container_conds, media_conds)."""
    q = q.strip()
    neg = False
    m = re.match(r"^not\s+all\s+and\s+(.*)$", q, re.I)
    if m:
        neg = True; q = m.group(1)
    feats = [x.strip() for x in re.split(r"\s+and\s+", q, flags=re.I) if x.strip()]
    cont, med = [], []
    for f in feats:
        kind, val = eval_feature(f, phone)
        if kind == "static":
            if not val:
                return ([], []) if neg else None   # not (false and ...) = always true; (false and ...) = never
            if neg and len(feats) == 1:
                return None                        # not (true) = never
            continue
        (cont if kind == "container" else med).append(val)
    if neg:
        if med or len(cont) != 1:
            raise ValueError("unsupported negated query: " + q)
        cont = ["not " + cont[0]]
    return (cont, med)


def keyframe_names(css):
    return set(re.findall(r"@(?:-webkit-)?keyframes\s+([\w-]+)", css))


def fix_decls(body, kf):
    def anim(m):
        val = m.group(2)
        for name in kf:
            val = re.sub(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", "pqs-" + name, val)
        return m.group(1) + val
    body = re.sub(r"((?:-webkit-)?animation(?:-name)?\s*:)([^;}]*)", anim, body)
    body = re.sub(r"(\d)vw\b", r"\1cqw", body)
    return body


def emit(items, root, phone, kf, wrap=None):
    out = []
    for pre, body in items:
        if body is None:
            if pre.lower().startswith("@charset") or pre.lower().startswith("@import"):
                continue
            continue
        low = pre.lower()
        if low.startswith("@media"):
            cond = pre[6:].strip()
            inner = parse(body)
            for q in split_top(cond):
                r = eval_query(q, phone)
                if r is None:
                    continue
                cont, med = r
                txt = "".join(emit(inner, root, phone, kf))
                if not txt.strip():
                    continue
                if cont:
                    txt = "@container pqs %s{%s}" % (" and ".join(cont), txt)
                if med:
                    txt = "@media %s{%s}" % (" and ".join(med), txt)
                out.append(txt)
        elif re.match(r"@(-webkit-)?keyframes", low):
            name = re.split(r"\s+", pre.strip(), maxsplit=1)[1].strip()
            out.append("@keyframes pqs-%s{%s}" % (name, body))
        elif low.startswith("@font-face") or low.startswith("@page"):
            continue
        elif low.startswith("@supports"):
            out.append("%s{%s}" % (pre, "".join(emit(parse(body), root, phone, kf))))
        elif low.startswith("@"):
            raise ValueError("unknown at-rule: " + pre[:40])
        else:
            sels = [scope_selector(s, root) for s in split_top(pre)]
            out.append("%s{%s}" % (",".join(sels), fix_decls(body.strip(), kf)))
    return out


def main(page, variant, root, out_path):
    phone = variant == "phone"
    html = open(page, encoding="utf-8").read()
    blocks = []
    for m in re.finditer(r"<style([^>]*)>(.*?)</style>", html, re.S):
        if 'id="pq-desktop-guard"' in m.group(1):
            continue                                  # the website's "open on a computer" guard: not part of the board
        blocks.append(m.group(2))
    css = strip_comments("\n".join(blocks))
    kf = keyframe_names(css)
    rules = emit(parse(css), root, phone, kf)
    out = "\n".join(rules)
    out = re.sub(r"[ \t]*\n[ \t]*", "\n", out)
    out = re.sub(r"\n{2,}", "\n", out)
    # The website fonts are embedded under panel-only names (gen_fonts.py FAMILY_MAP): point the sheet at them.
    for fam, panel_fam in (("Hanken Grotesk", "PQS Hanken Grotesk"), ("JetBrains Mono", "PQS JetBrains Mono"),
                           ("Bricolage Grotesque", "PQS Bricolage Grotesque")):
        out = re.sub(r"(['\"])%s\1" % re.escape(fam), "'%s'" % panel_fam, out)
    if "<" in out:
        raise ValueError("'<' found in generated CSS")   # never let anything close the <style> element
    open(out_path, "w", encoding="utf-8", newline="\n").write(out)
    print(out_path, len(out), "chars,", len(rules), "rules, keyframes:", sorted(kf))


if __name__ == "__main__":
    main(*sys.argv[1:5])
