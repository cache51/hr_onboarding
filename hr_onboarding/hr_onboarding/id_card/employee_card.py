"""Generate the RGM Đà Nẵng worker lanyard badge — "THẺ CÔNG NHÂN VIÊN".

Recreates the existing paper employee card (red crown logo, company header, photo,
name + MSNV + department + position + join date) as a self-contained PDF, plus a
QR (encoding the MSNV) so the same card doubles as the kiosk scan badge.

Portrait badge 80 × 120 mm, centred on an A4 page with a dashed cut guide — print
on A4, cut out, laminate. Distinct from `id_card.py` (the compact 9-up CR80 sheet).

WeasyPrint + segno are existing dependencies (leave PDF / id_card).
"""
from __future__ import annotations

import base64
import io
import pathlib
import re
from dataclasses import dataclass

import segno

_ASSETS = pathlib.Path(__file__).resolve().parent / "assets"
_COMPANY_LINE = "CÔNG TY TNHH MỘT THÀNH VIÊN"
_COMPANY_NAME = "RGM ĐÀ NẴNG"
_ADDRESS = "Lô 04, KCN Điện Nam - Điện Ngọc, Quảng Nam"
_PHONE = "ĐT: 0235.3745.666"
_CARD_TITLE = "THẺ CÔNG NHÂN VIÊN"


@dataclass(frozen=True)
class EmployeeCardData:
    employee_id: str
    employee_name: str
    department: str
    grade: str = ""
    designation: str = ""
    date_of_joining: str = ""
    photo_data_uri: str | None = None


# ── helpers ─────────────────────────────────────────────────────────────────

def _logo_data_uri() -> str | None:
    p = _ASSETS / "rgm-logo.png"
    return ("data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()) if p.exists() else None


def _qr_png_data_uri(msnv: str) -> str:
    """QR as a high-res PNG data URI.

    CRITICAL: micro=False. For short data like an MSNV, segno.make() defaults to a
    *Micro QR* code (a single finder pattern) — which phone cameras, jsQR, and
    html5-qrcode CANNOT read. We force a standard QR (three finder patterns).
    PNG (not inline SVG) because WeasyPrint can mis-render segno's SVG."""
    return "data:image/png;base64," + base64.b64encode(_qr_png_bytes(msnv)).decode()


def _qr_png_bytes(msnv: str) -> bytes:
    """Standard (micro=False) QR PNG bytes — for embedding in XLSX / images."""
    buf = io.BytesIO()
    segno.make(msnv, micro=False, error="m").save(
        buf, kind="png", scale=16, border=2, dark="#000", light="#fff",
    )
    return buf.getvalue()


# ERPNext stores many office departments un-accented ("KE HOACH") or in English
# ("Human Resources"); restore proper Vietnamese for the card. Codes/acronyms
# (KCS, PMC, FCA, IQC, IE, ERP, CBX, CBNM, KHO NPL) and already-accented names
# (THÀNH PHẨM 2, BAN GIÁM ĐỐC…) fall through unchanged. Confirm with HR if unsure.
_DEPT_MAP = {
    "CAT": "CẮT",
    "MAY MAU": "MAY MẪU",
    "UI CAT CHI": "ỦI CẮT CHỈ",
    "KE HOACH": "KẾ HOẠCH",
    "KY THUAT CONG NGHE": "KỸ THUẬT CÔNG NGHỆ",
    "KY THUAT TRIEN KHAI": "KỸ THUẬT TRIỂN KHAI",
    "TO TRUONG TO PHO": "TỔ TRƯỞNG - TỔ PHÓ",
    "TO CHUAN BI": "TỔ CHUẨN BỊ",
    "GAP XEP CHE HANG": "GẤP XẾP CHE HÀNG",
    "BAO TRI": "BẢO TRÌ",
    "TAP VU": "TẠP VỤ",
    "GIAO NHAN": "GIAO NHẬN",
    "CO DIEN": "CƠ ĐIỆN",
    "HUMAN RESOURCES": "NHÂN SỰ",
    "ACCOUNTS": "KẾ TOÁN",
}


def _dept_vi(dept: str) -> str:
    d = (dept or "").removesuffix(" - RDN").removesuffix(" - RHZ").strip()
    m = re.match(r"LINE\s+(\d+)", d, re.IGNORECASE)
    if m:
        return f"CHUYỀN {m.group(1)}"
    return _DEPT_MAP.get(d.upper(), d.upper())


def _position_vi(grade: str, designation: str) -> str:
    if "/" in (grade or ""):
        vi = grade.split("/", 1)[1].strip()
        if vi:
            return vi.upper()
    return (designation or grade or "").upper()


def _fmt_date(iso: str) -> str:
    try:
        y, m, d = iso.split("-")
        return f"{d}/{m}/{y}"
    except (ValueError, AttributeError):
        return iso or ""


# ── card HTML ────────────────────────────────────────────────────────────────

def _card_html(emp: EmployeeCardData) -> str:
    logo = _logo_data_uri()
    logo_html = (f'<img class="logo" src="{logo}" alt="RGM">'
                 if logo else '<span class="logo-fb">RR</span>')

    if emp.photo_data_uri:
        photo_html = f'<img class="photo-img" src="{emp.photo_data_uri}" alt="">'
    else:
        photo_html = '<div class="photo-ph"><div class="photo-ph-inner">ẢNH<br>3×4</div></div>'

    dept     = _dept_vi(emp.department)
    position = _position_vi(emp.grade, emp.designation)
    joined   = _fmt_date(emp.date_of_joining)

    return f"""<div class="card">

  <!-- header: logo left, company text centred -->
  <table class="head"><tr>
    <td class="head-logo">{logo_html}</td>
    <td class="head-text">
      <div class="co-line">{_COMPANY_LINE}</div>
      <div class="co-name">{_COMPANY_NAME}</div>
      <div class="co-addr">{_ADDRESS}</div>
      <div class="co-addr">{_PHONE}</div>
    </td>
  </tr></table>

  <div class="title">{_CARD_TITLE}</div>

  <div class="photo-wrap">{photo_html}</div>

  <div class="name">{emp.employee_name}</div>

  <div class="info">
    <div class="frow"><span class="fk">Mã số thẻ: </span><span class="fv fv-id">{emp.employee_id}</span></div>
    <div class="frow"><span class="fk">Bộ phận: </span><span class="fv">{dept}</span></div>
    <div class="frow"><span class="fk">Chức vụ: </span><span class="fv">{position}</span></div>
    <div class="frow"><span class="fk">Ngày vào làm: </span><span class="fv">{joined}</span></div>
  </div>

  <div class="qr-wrap">
    <img class="qr-img" src="{_qr_png_data_uri(emp.employee_id)}" alt="QR {emp.employee_id}">
    <div class="qr-cap">Quét tại kiosk · Scan at kiosk</div>
  </div>
</div>"""


# ── CSS ──────────────────────────────────────────────────────────────────────

_CSS = """
/* A4 page, card centred with a dashed cut guide — print on A4, cut out */
@page { size: A4 portrait; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "Noto Sans","DejaVu Sans",sans-serif; background: #fff;
  width: 210mm; height: 297mm; display: table;
}
.page-center { display: table-cell; width: 210mm; height: 297mm;
  vertical-align: middle; text-align: center; }
.cut-guide { display: inline-block; border: 0.4mm dashed #aaa; line-height: 0; }

.card {
  width: 80mm; height: 128mm;
  border: 0.6mm solid #111; border-radius: 2.5mm;
  padding: 3.5mm 4mm; text-align: center; color: #1a1a1a;
}

/* header */
.head { width: 100%; border-collapse: collapse; }
.head-logo { width: 16mm; vertical-align: middle; text-align: left; }
.logo { width: 14mm; height: auto; display: block; }
.logo-fb { font-weight: 900; color: #c1121f; font-size: 15pt; }
.head-text { vertical-align: middle; text-align: center; padding-left: 1mm; }
.co-line { font-size: 6.5pt; font-weight: 600; letter-spacing: .2px; }
.co-name { font-size: 15pt; font-weight: 800; line-height: 1.15; color: #0b2d6e; }
.co-addr { font-size: 6pt; color: #333; line-height: 1.45; }

.title {
  font-size: 11pt; font-weight: 800; letter-spacing: .3px;
  color: #0b2d6e; text-transform: uppercase;
  border-top: 0.3mm solid #ccc; border-bottom: 0.3mm solid #ccc;
  padding: 1mm 0; margin: 1.5mm 0 2mm;
}

/* photo */
.photo-wrap {
  width: 27mm; height: 34mm; margin: 0 auto 1.5mm;
  border: 0.4mm solid #999; border-radius: 1mm; overflow: hidden;
}
.photo-img { width: 100%; height: 100%; object-fit: cover; }
.photo-ph { display: table; width: 100%; height: 100%; background: #f0f2f5; }
.photo-ph-inner { display: table-cell; vertical-align: middle; text-align: center;
  color: #aaa; font-size: 6.5pt; line-height: 1.6; }

/* identity */
.name { font-size: 12pt; font-weight: 800; color: #111; line-height: 1.2; margin-bottom: 1.5mm; }
.info { margin-bottom: 2mm; }
.frow { font-size: 7pt; line-height: 1.6; }
.fk   { color: #666; font-weight: 500; }
.fv   { color: #111; font-weight: 700; }
.fv-id { font-family: "DejaVu Sans Mono","Courier New",monospace; }

/* QR — large for reliable camera scan */
.qr-wrap { margin-top: 0.5mm; }
.qr-img { width: 30mm; height: 30mm; display: block; margin: 0 auto; }
.qr-cap { font-size: 5.5pt; color: #555; font-weight: 600; margin-top: 1mm; letter-spacing: .2px; }
"""


# ── public API ───────────────────────────────────────────────────────────────

def build_employee_card_html(emp: EmployeeCardData) -> str:
    card = _card_html(emp)
    return (f'<!doctype html><html lang="vi"><head><meta charset="utf-8">'
            f'<style>{_CSS}</style></head>'
            f'<body><div class="page-center"><div class="cut-guide">{card}</div></div>'
            f'</body></html>')


def render_employee_card(emp: EmployeeCardData) -> bytes:
    """Render a single portrait worker badge (centred on A4) to PDF bytes."""
    from weasyprint import HTML  # noqa: PLC0415
    return HTML(string=build_employee_card_html(emp)).write_pdf()


# ── 9-up sheet (3×3 on A4) ───────────────────────────────────────────────────
# Same portrait design, scaled to a credit-card-ish 60 × 88 mm so nine fit on one
# A4. Print on plain A4, cut on the dashed guides, laminate + clip.

def _sheet_card_html(emp: EmployeeCardData) -> str:
    logo = _logo_data_uri()
    logo_html = (f'<img class="s-logo" src="{logo}" alt="RGM">'
                 if logo else '<span class="s-logo-fb">RR</span>')
    if emp.photo_data_uri:
        photo_html = f'<img class="s-photo-img" src="{emp.photo_data_uri}" alt="">'
    else:
        photo_html = '<div class="s-photo-ph"><div class="s-photo-inner">ẢNH<br>3×4</div></div>'

    joined = _fmt_date(emp.date_of_joining)
    # Join date appended to the MSNV line, separated by " / " (the date is rendered
    # in a lighter style so the MSNV stays the prominent value).
    msnv_val = (f'{emp.employee_id}<span class="s-since"> / {joined}</span>'
                if joined else emp.employee_id)
    return f"""<div class="s-card">
  <div class="s-head">
    <div class="s-head-logo">{logo_html}</div>
    <div class="s-head-text">
      <div class="s-co-name">{_COMPANY_NAME}</div>
      <div class="s-co-sub">{_CARD_TITLE}</div>
    </div>
  </div>
  <div class="s-photo">{photo_html}</div>
  <div class="s-name">{emp.employee_name}</div>
  <div class="s-info">
    <div><span class="s-fk">MSNV: </span><span class="s-fv s-id">{msnv_val}</span></div>
    <div><span class="s-fk">Bộ phận: </span><span class="s-fv">{_dept_vi(emp.department)}</span></div>
    <div><span class="s-fk">Chức vụ: </span><span class="s-fv">{_position_vi(emp.grade, emp.designation)}</span></div>
  </div>
  <img class="s-qr" src="{_qr_png_data_uri(emp.employee_id)}" alt="QR {emp.employee_id}">
</div>"""


_SHEET_CSS = """
/* True portrait CR80 cards (54 × 85.6 mm), 3×3 on A4.
   Grid = 3×54 + 2×2 = 166mm wide, 3×85.6 + 2×2 = 260.8mm tall — leaving ~22mm
   side / ~18mm top margins so a printer never needs to scale (print at 100%). */
@page { size: A4 portrait; margin: 16mm 20mm; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Noto Sans","DejaVu Sans",sans-serif; background: #fff; }

.sheet { border-collapse: separate; border-spacing: 2mm; margin: 0 auto; }
.sheet td { width: 54mm; height: 85.6mm; padding: 0; vertical-align: top;
            outline: 0.3mm dashed #bbb; }

.s-card {
  width: 54mm; height: 85.6mm;
  border: 0.5mm solid #111; border-radius: 2mm;
  padding: 1.6mm; text-align: center; overflow: hidden;
}

/* header — display:table divs (NOT a <table> element; that clips inside a grid td) */
.s-head { display: table; width: 100%; }
.s-head-logo { display: table-cell; width: 11mm; vertical-align: middle; text-align: left; }
.s-logo { width: 10mm; height: auto; display: block; }
.s-logo-fb { font-weight: 900; color: #c1121f; font-size: 11pt; }
.s-head-text { display: table-cell; vertical-align: middle; text-align: center; }
.s-co-name { font-size: 12pt; font-weight: 800; color: #0b2d6e; line-height: 1.0; }
.s-co-sub  { font-size: 5.5pt; font-weight: 700; color: #0b2d6e; letter-spacing: .2px;
             text-transform: uppercase; margin-top: .3mm; }

/* photo — pulled up + slightly smaller so the QR below always clears the bottom */
.s-photo { width: 17mm; height: 21mm; margin: .4mm auto .6mm;
           border: 0.4mm solid #999; border-radius: 1mm; overflow: hidden; }
.s-photo-img { width: 100%; height: 100%; object-fit: cover; }
.s-photo-ph { display: table; width: 100%; height: 100%; background: #f0f2f5; }
.s-photo-inner { display: table-cell; vertical-align: middle; text-align: center;
                 color: #aaa; font-size: 5pt; line-height: 1.5; }

/* identity */
.s-name { font-size: 9.5pt; font-weight: 800; color: #111; line-height: 1.1; margin-bottom: .6mm; }
.s-info { margin-bottom: .6mm; }
.s-info > div { font-size: 6.5pt; line-height: 1.4; }
.s-fk { color: #666; font-weight: 500; }
.s-fv { color: #111; font-weight: 700; }
.s-id { font-family: "DejaVu Sans Mono","Courier New",monospace; }
.s-since { color: #888; font-weight: 600; }   /* join date appended after MSNV */

/* QR — 26mm; sits in the cleared space with margin to spare (never clipped) */
.s-qr { width: 26mm; height: 26mm; display: block; margin: 0 auto; }
"""


def build_employee_card_sheet_html(employees: list[EmployeeCardData]) -> str:
    """A4 sheet with up to 9 portrait cards in a 3-column grid."""
    emps: list[EmployeeCardData | None] = list(employees)
    while len(emps) % 3:
        emps.append(None)
    rows = []
    for i in range(0, len(emps), 3):
        cells = "".join(
            f"<td>{_sheet_card_html(emps[i + j]) if emps[i + j] else ''}</td>"
            for j in range(3)
        )
        rows.append(f"<tr>{cells}</tr>")
    return (f'<!doctype html><html lang="vi"><head><meta charset="utf-8">'
            f'<style>{_SHEET_CSS}</style></head>'
            f'<body><table class="sheet">{"".join(rows)}</table></body></html>')


def render_employee_card_sheet(employees: list[EmployeeCardData]) -> bytes:
    """Render up to 9 cards per A4 page to PDF bytes via WeasyPrint."""
    from weasyprint import HTML  # noqa: PLC0415
    return HTML(string=build_employee_card_sheet_html(employees)).write_pdf()


# ── 9-up sheet, FORM layout (matches HR's XLSX) ──────────────────────────────
# Left-aligned company header top-left, QR floated top-right, "THẺ CÔNG NHÂN VIÊN"
# centred below, then photo, name, and centred info — i.e. the same arrangement as
# the THẺ_RGM_with_QR.xlsx template, at CR80 (54 × 85.6 mm), 9 per A4.

_FORM_COMPANY_LINE = "CÔNG TY TNHH MTV"
_FORM_ADDRESS = "Lô 04, KCN Điện Nam - Điện Ngọc, ĐN"   # full address, as in the XLS


def _form_card_html(emp: EmployeeCardData) -> str:
    logo = _logo_data_uri()
    logo_html = (f'<img class="f-logo" src="{logo}" alt="RGM">' if logo
                 else '<span class="f-logo-fb">RR</span>')
    if emp.photo_data_uri:
        photo = f'<img class="f-photo-img" src="{emp.photo_data_uri}" alt="">'
    else:
        photo = '<div class="f-photo-ph"><div class="f-photo-inner">ẢNH<br>3×4</div></div>'
    return f"""<div class="f-card">
  <img class="f-qr" src="{_qr_png_data_uri(emp.employee_id)}" alt="QR">
  <div class="f-top">
    <div class="f-head">
      <div class="f-head-logo">{logo_html}</div>
      <div class="f-head-text"><div class="f-co-shift">
        <div class="f-co-line">{_FORM_COMPANY_LINE}</div>
        <div class="f-co-name">{_COMPANY_NAME}</div>
        <div class="f-co-addr">{_FORM_ADDRESS}</div>
        <div class="f-co-addr">{_PHONE}</div>
      </div></div>
    </div>
    <div class="f-title">{_CARD_TITLE}</div>
  </div>
  <div class="f-bottom">
    <div class="f-photo">{photo}</div>
    <div class="f-ident">
      <div class="f-name">{emp.employee_name}</div>
      <div class="f-info">
        <div><span class="f-fk">Mã số thẻ: </span><span class="f-fv f-id">{emp.employee_id}</span></div>
        <div><span class="f-fk">Bộ phận: </span><span class="f-fv">{_dept_vi(emp.department)}</span></div>
        <div><span class="f-fk">Chức vụ: </span><span class="f-fv">{_position_vi(emp.grade, emp.designation)}</span></div>
        <div><span class="f-fk">Ngày vào làm: </span><span class="f-fv">{_fmt_date(emp.date_of_joining)}</span></div>
      </div>
    </div>
  </div>
</div>"""


# Exact XLS font sizes (Times New Roman bold): header 5pt, title 14pt, name 13pt,
# Mã số thẻ 10pt, Bộ phận 9pt, Chức vụ 11pt, Ngày vào làm 10pt. Card 64×93mm so 9
# still fit on A4 while keeping those sizes; logo top-left, QR top-right.
_FORM_SHEET_CSS = """
@page { size: A4 portrait; margin: 5mm 0 0 0; }   /* top margin so printers don't clip the top row */
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Times New Roman","DejaVu Serif",serif; background: #fff; }

.sheet { border-collapse: separate; border-spacing: 4mm 5mm; margin: 0 auto; }
.sheet td { width: 63mm; height: 85mm; padding: 0; vertical-align: top; }
/* Multi-page master sheets (788 cards ≈ 88 pages): never split a row of 3 cards
   across a page break — each row moves whole to the next page. */
.sheet tr { break-inside: avoid; page-break-inside: avoid; }

.f-card { width: 63mm; height: 85mm; border: 0.5mm solid #111; border-radius: 2mm;
          padding: 2.5mm; overflow: hidden; position: relative;
          break-inside: avoid; page-break-inside: avoid; }
/* QR floated in the top-right corner, OUT of the header flow so the address can
   never push it off the edge. */
.f-qr { position: absolute; top: 2.5mm; right: 2.5mm; width: 19mm; height: 19mm; }

/* the header block + title, nudged up 6pt as a group */
.f-top { position: relative; top: 0; }
/* photo + name + info, nudged down 6pt as a group */
.f-bottom { position: relative; top: 0; }
/* name + info nudged a further 9pt down (photo stays) */
.f-ident { position: relative; top: 0; }

/* header: logo | text (5pt) | QR top-right. table-layout:fixed keeps the QR cell's
   width so the long address can never push the QR off the card edge. */
/* header: logo + company text on the left (the QR is absolute, top-right). The
   header table reserves only ~37mm so the text never reaches under the QR. */
/* header cells aligned to the TOP so the logo + company text start level with the
   top of the QR (not hanging down to the QR's bottom edge). */
.f-head { display: table; width: 34mm; table-layout: fixed; border-spacing: 0; }
.f-head-logo { display: table-cell; width: 13mm; vertical-align: top; text-align: left; }
.f-logo { width: 13mm; height: auto; display: block; }
.f-logo-fb { font-weight: 900; color: #c1121f; font-size: 13pt; }
/* text column kept narrow (≈21mm) so the long address WRAPS to two short lines
   that end well left of the QR — no more grazing the QR corner. */
.f-head-text { display: table-cell; width: 21mm; vertical-align: top; text-align: left; }
.f-co-shift { transform: translateX(-1mm); }   /* small left nudge toward the logo */
.f-co-line { font-size: 5pt; font-weight: 700; line-height: 1.6; white-space: nowrap; }
.f-co-name { font-size: 5pt; font-weight: 700; line-height: 1.6; white-space: nowrap; }
.f-co-addr { font-size: 5pt; font-weight: 700; line-height: 1.6; }  /* address wraps to 2 lines */

/* the header was raised ~9mm (cells no longer pushed down by inherited border-spacing)
   so it tops out level with the QR; add that gap back above the title so the title +
   photo + identity block stay exactly where they were before. */
.f-title { font-size: 11pt; font-weight: 700; text-align: center; margin: 5mm 0 1mm 0;
           position: relative; top: -2pt; }   /* margin reclaimed so a 2-line name fits */

/* photo — trimmed slightly (30→27mm) to make room for 2-line names */
.f-photo { width: 24mm; height: 27mm; margin: 0 auto 1mm;
           border: 0.4mm solid #999; overflow: hidden; }
.f-photo-img { width: 100%; height: 100%; object-fit: cover; }
.f-photo-ph { display: table; width: 100%; height: 100%; background: #f5f5f5; }
.f-photo-inner { display: table-cell; vertical-align: middle; text-align: center;
                 color: #aaa; font-size: 6pt; line-height: 1.5; }

/* identity — centred, exact XLS sizes */
.f-name { font-size: 11pt; font-weight: 700; text-align: center; line-height: 1.05; margin-bottom: .8mm; }
.f-info { text-align: center; }
.f-info > div { font-weight: 700; line-height: 1.3; }
.f-info > div:nth-child(1) { font-size: 8pt; }
.f-info > div:nth-child(2) { font-size: 7pt; }
.f-info > div:nth-child(3) { font-size: 9pt; }
.f-info > div:nth-child(4) { font-size: 8pt; }
.f-fk { font-weight: 700; }
.f-fv { font-weight: 700; }
.f-id { font-family: inherit; }
"""


def build_employee_card_sheet_form_html(employees: list[EmployeeCardData]) -> str:
    """A4 sheet, FORM layout (XLSX-style), up to 9 cards in a 3-column grid."""
    emps: list[EmployeeCardData | None] = list(employees)
    while len(emps) % 3:
        emps.append(None)
    rows = []
    for i in range(0, len(emps), 3):
        cells = "".join(
            f"<td>{_form_card_html(emps[i + j]) if emps[i + j] else ''}</td>"
            for j in range(3)
        )
        rows.append(f"<tr>{cells}</tr>")
    return (f'<!doctype html><html lang="vi"><head><meta charset="utf-8">'
            f'<style>{_FORM_SHEET_CSS}</style></head>'
            f'<body><table class="sheet">{"".join(rows)}</table></body></html>')


def render_employee_card_sheet_form(employees: list[EmployeeCardData]) -> bytes:
    """Render the FORM-layout (XLSX-style) 9-up sheet to PDF bytes."""
    from weasyprint import HTML  # noqa: PLC0415
    return HTML(string=build_employee_card_sheet_form_html(employees)).write_pdf()
