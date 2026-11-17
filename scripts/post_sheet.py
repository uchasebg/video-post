r"""Measuring and tracking for video posts (content\video-posts\video-posts.xlsx).

Commands:
  python post_sheet.py measure <post.json>              print hook / VO / description measurements, no writing
  python post_sheet.py add     <post.json> [--no-open]  append a row (number assigned automatically)
  python post_sheet.py update  <n> <post.json> [--no-open]   overwrite only the fields present in the JSON
  python post_sheet.py show    <n>                      print one row
  python post_sheet.py check                            measure every row already in the sheet
  python post_sheet.py format [--no-open]               repair the view: column widths, fixed row
                                                        height, wrapped cells, freeze panes, top-left

post.json keys (all optional for update):
  date        publication / occasion date, "2026-12-06"
  topic       the topic
  type        video or card ("video" / "kartichka"); inferred from an empty vo when omitted
  hook        the hook (the yellow banner)
  alt_hooks   the two alternatives, one per line
  vo          the voice over script (empty or "-" for a static card)
  desc        the description
  sources     the checked sources, free text
  lang        translation language, "IT" / "RO" / "PL" ...
  hook_tr     the translated hook
  vo_tr       the translated voice over
  desc_tr     the translated description
  status      one of STATUSES
  notes       notes

Before writing, the script saves and closes the workbook if it is open in Excel (that workbook
only), edits the file in place so the user's own edits survive, and reopens it. Those two steps
are Windows-only and are skipped elsewhere. A description over 2,200 characters is refused.
Characters are counted in UTF-16 units, so an emoji counts as 2 -- the way Instagram and
Facebook count.

The sheet location is resolved at run time (see sheet_path), so the skill works on any machine.
"""
import json
import os
import re
import subprocess
import sys

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation


def sheet_path():
    """Where the tracking sheet lives, resolved so the skill works on any machine.

    1. $VIDEO_POSTS_SHEET, if set -- the escape hatch for a non-standard layout.
    2. The nearest `content` folder at or above the working directory.
    3. `content/video-posts/video-posts.xlsx` under the working directory (created on first write).
    """
    env = os.environ.get("VIDEO_POSTS_SHEET")
    if env:
        return os.path.abspath(env)
    cur = os.path.abspath(os.getcwd())
    while True:
        if os.path.isdir(os.path.join(cur, "content")):
            return os.path.join(cur, "content", "video-posts", "video-posts.xlsx")
        parent = os.path.dirname(cur)
        if parent == cur:
            return os.path.join(os.getcwd(), "content", "video-posts", "video-posts.xlsx")
        cur = parent


PATH = sheet_path()
TAB = "Видео постове"
DESC_LIMIT = 2200

# Targets from style-guide.md, measured on the user's 12 reference posts.
HOOK_WORDS = (4, 9)
HOOK_CHARS = (20, 55)
VO_WORDS = (25, 40)
DESC_CHARS = (1100, 2100)
# A static card is a different format: the hook is a greeting and the caption is short on purpose.
CARD_HOOK_WORDS = (1, 6)
CARD_HOOK_CHARS = (6, 40)
CARD_DESC_CHARS = (400, 900)
# Bulgarian narration with pauses. The middle value is the one quoted to the user; the outer two
# show how much the estimate moves with the speaker's pace.
PACES = (2.3, 2.6, 3.0)

H_NUM, H_DATE, H_TOPIC, H_TYPE = "№", "Дата", "Тема", "Тип"
H_HOOK, H_ALT = "Хук", "Алтернативни хукове"
H_VO, H_DESC = "Voice over", "Описание"
H_VOW, H_VOS, H_DESCC = "VO думи", "VO сек", "Описание знаци"
H_SRC, H_LANG = "Източници", "Език на превод"
H_HOOK_TR, H_VO_TR, H_DESC_TR = "Хук (превод)", "Voice over (превод)", "Описание (превод)"
H_STATUS, H_NOTES = "Статус", "Бележки"

HEADERS = [H_NUM, H_DATE, H_TOPIC, H_TYPE, H_HOOK, H_ALT, H_VO, H_DESC,
           H_VOW, H_VOS, H_DESCC, H_SRC, H_LANG, H_HOOK_TR, H_VO_TR, H_DESC_TR,
           H_STATUS, H_NOTES]
KEYS = {"date": H_DATE, "topic": H_TOPIC, "type": H_TYPE, "hook": H_HOOK, "alt_hooks": H_ALT,
        "vo": H_VO, "desc": H_DESC, "sources": H_SRC, "lang": H_LANG, "hook_tr": H_HOOK_TR,
        "vo_tr": H_VO_TR, "desc_tr": H_DESC_TR, "status": H_STATUS, "notes": H_NOTES}
STATUSES = ["Чернова", "Одобрен", "Преведен", "Публикуван", "Отказан"]
WIDTHS = {H_NUM: 5, H_DATE: 12, H_TOPIC: 22, H_TYPE: 10, H_HOOK: 34, H_ALT: 40,
          H_VO: 55, H_DESC: 70, H_VOW: 8, H_VOS: 8, H_DESCC: 10, H_SRC: 34, H_LANG: 9,
          H_HOOK_TR: 34, H_VO_TR: 55, H_DESC_TR: 70, H_STATUS: 14, H_NOTES: 30}

THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
ROW_HEIGHT = 120  # readable without breaking wheel scrolling; same compromise as rtm_sheet.py
FREEZE = "B2"


def ulen(s):
    """UTF-16 code units, the way Instagram and Facebook count characters."""
    return len((s or "").encode("utf-16-le")) // 2


def words(s):
    return len([w for w in re.split(r"\s+", (s or "").strip()) if w])


def is_card(data):
    vo = (data.get("vo") or "").strip()
    t = str(data.get("type", "")).strip().lower()
    return t.startswith(("card", "карт")) or vo in ("", "—", "-")


def flag(n, lo, hi):
    return "" if lo <= n <= hi else ("  ПОД целта" if n < lo else "  НАД целта")


def report(data, label=""):
    hook, vo, desc = data.get("hook", ""), data.get("vo", ""), data.get("desc", "")
    card = is_card(data)
    out = [f"=== {label or data.get('topic', '')}" + ("  [статична картичка]" if card else "")]
    hw, hc = words(hook), ulen(hook)
    hwr, hcr = (CARD_HOOK_WORDS, CARD_HOOK_CHARS) if card else (HOOK_WORDS, HOOK_CHARS)
    out.append(f"Хук:       {hw} думи{flag(hw, *hwr)} / {hc} знака{flag(hc, *hcr)}")
    if card:
        out.append("Voice over: — (статична картичка)")
    else:
        vw = words(vo)
        secs = " / ".join(f"{vw / p:.0f}" for p in PACES)
        out.append(f"Voice over: {vw} думи{flag(vw, *VO_WORDS)} / {ulen(vo)} знака"
                   f"  ≈ {secs} сек (при {PACES[0]} / {PACES[1]} / {PACES[2]} думи/сек)")
    dc = ulen(desc)
    pars = len([p for p in (desc or "").split("\n") if p.strip()])
    over = ("  ОТКАЗАНО: над лимита от 2200" if dc > DESC_LIMIT
            else flag(dc, *(CARD_DESC_CHARS if card else DESC_CHARS)))
    out.append(f"Описание:  {dc} знака{over} / {pars} абзаца")
    for key, lbl in (("hook_tr", "Хук (превод)"), ("vo_tr", "VO (превод)"),
                     ("desc_tr", "Описание (превод)")):
        if data.get(key):
            extra = f"  ≈ {words(data[key]) / PACES[1]:.0f} сек" if key == "vo_tr" else ""
            out.append(f"{lbl}: {words(data[key])} думи / {ulen(data[key])} знака{extra}")
    return "\n".join(out)


def build_tab(ws):
    for i, name in enumerate(HEADERS, 1):
        c = ws.cell(row=1, column=i, value=name)
        c.font = Font(bold=True, color="FFFFFF", size=11)
        c.fill = PatternFill("solid", fgColor="2E75B6" if "превод" in name else "1F3864")
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        c.border = BORDER
        ws.column_dimensions[c.column_letter].width = WIDTHS.get(name, 30)
    ws.row_dimensions[1].height = 32
    ws.freeze_panes = FREEZE
    ws.auto_filter.ref = f"A1:{ws.cell(row=1, column=len(HEADERS)).column_letter}1"
    letter = ws.cell(row=1, column=HEADERS.index(H_STATUS) + 1).column_letter
    dv = DataValidation(type="list", formula1='"' + ",".join(STATUSES) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{letter}2:{letter}500")


def fix_view(ws):
    for c in ws[1]:
        ws.column_dimensions[c.column_letter].width = WIDTHS.get(str(c.value), 30)
    for r in range(2, ws.max_row + 1):
        ws.row_dimensions[r].height = ROW_HEIGHT
        for c in ws[r]:
            c.alignment = WRAP
            c.border = BORDER
    ws.freeze_panes = FREEZE
    for view in ws.views.sheetView:
        view.topLeftCell = "A1"
        view.selection = []


def load():
    if not os.path.exists(PATH):
        os.makedirs(os.path.dirname(PATH), exist_ok=True)
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        build_tab(wb.create_sheet(TAB))
        return wb
    return openpyxl.load_workbook(PATH)


def close_in_excel():
    """Save and close this one workbook if Excel has it open. Windows only; a no-op elsewhere."""
    if sys.platform != "win32":
        return
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "try { $xl=[Runtime.InteropServices.Marshal]::GetActiveObject('Excel.Application');"
         f" foreach($wb in @($xl.Workbooks)){{ if($wb.FullName -eq '{PATH}'){{ $wb.Save(); $wb.Close($false) }} }} }} catch {{ }}"],
        capture_output=True, text=True)


def reopen():
    """Open the workbook again after writing. Windows only; a no-op elsewhere."""
    if sys.platform == "win32":
        os.startfile(PATH)
    else:
        print(f"(not reopened automatically on this platform: {PATH})")


def read_json(p):
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)


def write_row(ws, r, data):
    col = {c.value: i + 1 for i, c in enumerate(ws[1])}
    for key, header in KEYS.items():
        if key in data:
            ws.cell(row=r, column=col[header], value=data[key])
    if "vo" in data or "desc" in data:
        cur = {k: (data.get(k) if k in data else ws.cell(row=r, column=col[h]).value)
               for k, h in (("vo", H_VO), ("desc", H_DESC), ("type", H_TYPE))}
        vw = 0 if is_card(cur) else words(cur["vo"])
        ws.cell(row=r, column=col[H_VOW], value=vw or None)
        ws.cell(row=r, column=col[H_VOS], value=round(vw / PACES[1]) if vw else None)
        ws.cell(row=r, column=col[H_DESCC], value=ulen(cur["desc"]) or None)
    fix_view(ws)


def row_data(ws, r):
    """The row as it now stands in the sheet, so a partial update still reports the whole post."""
    col = {c.value: c.column for c in ws[1]}
    return {k: ws.cell(row=r, column=col[h]).value or "" for k, h in KEYS.items() if h in col}


def find_row(ws, n):
    for r in range(2, ws.max_row + 1):
        if ws.cell(row=r, column=1).value == n:
            return r
    sys.exit(f"ред № {n} не е намерен")


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    no_open = "--no-open" in sys.argv
    cmd = a[0] if a else ""

    if cmd == "measure":
        print(report(read_json(a[1])))
        return

    if cmd == "format":
        close_in_excel()
        wb = load()
        ws = wb[TAB]
        fix_view(ws)
        wb.save(PATH)
        print(f"format: {ws.max_row - 1} реда, височина {ROW_HEIGHT}pt, freeze panes {FREEZE}, превъртяно в началото")
        if not no_open:
            reopen()
        return

    if cmd == "check":
        ws = load()[TAB]
        for r in range(2, ws.max_row + 1):
            if not ws.cell(row=r, column=1).value:
                continue
            d = row_data(ws, r)
            print(report(d, f"№{ws.cell(row=r, column=1).value} {d.get('topic', '')}") + "\n")
        return

    if cmd == "show":
        ws = load()[TAB]
        r = find_row(ws, int(a[1]))
        for c in ws[1]:
            v = ws.cell(row=r, column=c.column).value
            if v not in (None, ""):
                print(f"=== {c.value}\n{v}\n")
        return

    if cmd not in ("add", "update"):
        sys.exit(__doc__)

    data = read_json(a[-1])
    for key in ("desc", "desc_tr"):
        if data.get(key) and ulen(data[key]) > DESC_LIMIT:
            sys.exit(f"ОТКАЗАНО: {key} е {ulen(data[key])} знака, лимитът е {DESC_LIMIT}")

    close_in_excel()
    wb = load()
    ws = wb[TAB]
    if cmd == "add":
        nums = [ws.cell(row=r, column=1).value for r in range(2, ws.max_row + 1)]
        n = max([x for x in nums if isinstance(x, int)], default=0) + 1
        r = ws.max_row + 1
        ws.cell(row=r, column=1, value=n)
        data.setdefault("status", STATUSES[0])
        data.setdefault("type", "картичка" if is_card(data) else "видео")
    else:
        n = int(a[1])
        r = find_row(ws, n)
    write_row(ws, r, data)
    wb.save(PATH)
    print(f"{cmd}: №{n} записан в {PATH}")
    print(report(row_data(ws, r)))
    if not no_open:
        reopen()


if __name__ == "__main__":
    main()
