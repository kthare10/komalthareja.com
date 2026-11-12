#!/usr/bin/env python3
"""Check the ordering of the Publications section in index.html.

Rules (the order on the page is the order in the file; nothing sorts at runtime):
  1. Every <li> in the Publications section carries data-date="YYYY-MM-DD".
  2. Each entry sits under the year heading matching its data-date year,
     and year groups run newest-first.
  3. Within a year, entries run newest-first by data-date.
  4. Tie-break for the same data-date: Komal's first-author papers first,
     then alphabetical by title (case-insensitive, ignoring a leading
     "(POSTER)" / "(WORK IN PROGRESS)" style tag).

Usage:  python3 tools/check_pub_order.py [path/to/index.html]
Exits 0 when the order is correct, 1 otherwise (and prints the expected order).
"""
import html
import re
import sys

ME = "Komal Thareja"


def strip(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def sort_key(e):
    # newest date first, then first-author, then title A-Z
    return (-int(e["date"].replace("-", "")), 0 if e["first"] else 1, e["sortable_title"])


def main(path):
    text = open(path, encoding="utf-8").read()
    start = text.find('<section id="publications"')
    end = text.find("</section>", start)
    if start < 0 or end < 0:
        print("Publications section not found")
        return 1
    section = text[start:end]

    errors = []
    years = []
    checked = 0
    for m in re.finditer(r'<h3[^>]*>\s*(\d{4})\s*</h3>(.*?)</ol>', section, re.S):
        year, body = m.group(1), m.group(2)
        checked += len(re.findall(r"<li[\s>]", body))
        entries = []
        for li in re.finditer(r"<li(?P<attrs>[^>]*)>(?P<body>.*?)</li>", body, re.S):
            d = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', li.group("attrs"))
            title_m = re.search(r'<p class="font-medium[^"]*">(.*?)</p>', li.group("body"), re.S)
            authors_m = re.search(r'<p class="mt-1 text-sm text-slate-600">(.*?)</p>', li.group("body"), re.S)
            title = strip(title_m.group(1)) if title_m else "?"
            if not d:
                errors.append(f"[{year}] missing data-date: {title}")
                continue
            authors = strip(authors_m.group(1)) if authors_m else ""
            entries.append({
                "date": d.group(1),
                "title": title,
                "first": authors.startswith(ME),
                "sortable_title": re.sub(r"^\([^)]*\)\s*", "", title).lower(),
            })
            if d.group(1)[:4] != year:
                errors.append(f"[{year}] dated {d.group(1)} but listed under {year}: {title}")
        years.append(year)

        expected = sorted(entries, key=sort_key)
        if [e["title"] for e in entries] != [e["title"] for e in expected]:
            errors.append(f"[{year}] out of order. Expected:")
            errors += [f"    {e['date']}  {'*' if e['first'] else ' '} {e['title']}" for e in expected]

    # Catch entries outside any "<h3>YYYY</h3> ... </ol>" group, which the loop above never sees.
    total = len(re.findall(r"<li[\s>]", section))
    if total != checked:
        errors.append(f"{total - checked} publication <li> entries are not inside a year group "
                      f"(found {total}, checked {checked})")

    if years != sorted(years, reverse=True):
        errors.append(f"Year groups not newest-first: {years}")

    if errors:
        print("\n".join(errors))
        print("(* = first-author)")
        return 1
    print(f"OK: {len(years)} year groups, publication order is correct.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "index.html"))
