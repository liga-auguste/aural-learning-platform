import csv
from pathlib import Path
from django.utils.text import slugify
from modules.models import Module

path = Path("imports/modules_import.csv")

with path.open(encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter=";")
    rows = []
    for r in reader:
        rr = {}
        for k, v in r.items():
            kk = (k or "").strip()
            rr[kk] = (v or "")
        rows.append(rr)

modules = []
current = None

def flush_current(curr):
    if not curr:
        return
    inclass = "\n".join(curr["inclass_parts"]).strip()
    homework = "\n".join(curr["homework_parts"]).strip()
    tags_raw = ",".join(curr["tags_parts"]).strip()
    modules.append({
        "title": curr["title"],
        "inclass": inclass,
        "homework": homework or None,
        "tags_raw": tags_raw,
    })

for r in rows:
    title = (r.get("title") or "").strip()
    inclass = (r.get("inclass") or "").strip()
    homework = (r.get("homework") or "").strip()
    tags = (r.get("tags") or "").strip()

    if title:
        flush_current(current)
        if len(modules) >= 10:
            break
        current = {"title": title, "inclass_parts": [], "homework_parts": [], "tags_parts": []}

    if not current:
        continue

    if inclass:
        current["inclass_parts"].append(inclass)
    if homework:
        current["homework_parts"].append(homework)
    if tags:
        current["tags_parts"].append(tags)

if len(modules) < 10:
    flush_current(current)

created = 0
updated = 0

for data in modules:
    title = data["title"]
    slug = slugify(title)

    obj, was_created = Module.objects.update_or_create(
        slug=slug,
        defaults={"title": title, "inclass": data["inclass"], "homework": data["homework"]},
    )

    tags_list = []
    if data["tags_raw"]:
        for t in data["tags_raw"].split(","):
            t = t.strip()
            if t:
                tags_list.append(t)
    obj.terms.set(tags_list)

    created += int(was_created)
    updated += int(not was_created)

print("prepared:", len(modules))
print((created, updated))
