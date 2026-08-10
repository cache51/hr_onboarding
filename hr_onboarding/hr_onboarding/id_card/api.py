# -*- coding: utf-8 -*-
"""Employee ID card printing.

Vendored, HR-approved renderer (``employee_card.py``) exposed as a whitelisted
endpoint. Reads the Employee master directly and returns the approved 3x3 FORM
card (``render_employee_card_sheet_form``) as a PDF download.

The card layout/size/look is intentionally untouched — see
``employee_card.py`` (copied verbatim from rgm-leave-app).
"""
from __future__ import unicode_literals

import base64
import re

import frappe
from frappe import _

from hr_onboarding.hr_onboarding.id_card.employee_card import (
	EmployeeCardData,
	render_employee_card_sheet_form,
)


def _photo_data_uri(image_url):
	"""Resolve an Employee.image URL to a base64 data URI, or None.

	``image`` is an Attach-Image field: ``/files/…`` (public) or
	``/private/files/…`` (private). We look the File doc up by ``file_url`` and
	read its bytes. Any problem (missing file, permission, unreadable) falls
	back to None so the card renders the approved blank "ẢNH 3×4" box.
	"""
	if not image_url:
		return None
	try:
		file_name = frappe.db.get_value("File", {"file_url": image_url}, "name")
		if not file_name:
			return None
		content = frappe.get_doc("File", file_name).get_content()
		if not content:
			return None
		mime = "image/png" if image_url.lower().endswith(".png") else "image/jpeg"
		return "data:%s;base64,%s" % (mime, base64.b64encode(content).decode())
	except Exception:
		# Never let a photo problem break card generation.
		frappe.log_error(
			title="ID card: photo resolve failed",
			message=frappe.get_traceback(),
		)
		return None


@frappe.whitelist()
def print_employee_id_card(employee):
	"""Render one Employee's approved ID card and return it as a PDF download.

	Read-only: reads the Employee master and renders. Gated by the standard
	Employee "read" permission (HR roles / System Manager).
	"""
	if not employee:
		frappe.throw(_("Employee is required"))

	# Permission gate — respects ERPNext's Employee read permission.
	if not frappe.has_permission("Employee", "read", doc=employee):
		raise frappe.PermissionError(_("Not permitted to read this Employee"))

	pdf = generate_employee_card_pdf(employee)

	frappe.local.response.filename = "ID-%s.pdf" % employee
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "download"


def generate_employee_card_pdf(employee):
	"""Build the approved ID card for one Employee and return the PDF bytes.

	Pure render helper (no permission check, no HTTP response) — reused by the
	whitelisted method and callable directly for tests/scripts.
	"""
	return render_employee_card_sheet_form([_card_data(frappe.get_doc("Employee", employee))])


def _card_data(doc):
	"""Employee doc → EmployeeCardData (shared by single + batch)."""
	return EmployeeCardData(
		employee_id=doc.name,
		employee_name=doc.employee_name or "",
		department=doc.department or "",
		grade=doc.grade or "",
		designation=doc.designation or "",
		date_of_joining=str(doc.date_of_joining or ""),
		photo_data_uri=_photo_data_uri(doc.image),
	)


# A batch renders in-request (WeasyPrint), roughly linear in card count; the full
# 788-employee master took minutes offline. Cap web batches so a stray wide range
# can't hit the gateway timeout — HR narrows the filter instead.
MAX_BATCH_CARDS = 200


@frappe.whitelist()
def print_employee_id_cards(codes=None, from_code=None, to_code=None,
                            from_joining=None, to_joining=None):
	"""Render ID cards for MANY employees as one 9-up A4 PDF (HR request 10 Aug
	2026, item 5: "print more than 1 card / 1 time").

	Exactly one selector must be provided:
	  codes         — MSNVs separated by comma / space / newline ("R00002, R00005")
	  from_code     + to_code     — inclusive MSNV range (e.g. R00002 → R00050)
	  from_joining  + to_joining  — inclusive date_of_joining range (YYYY-MM-DD)

	Only Active employees are included. An explicit `codes` list that names an
	unknown or inactive employee FAILS with the offending codes listed — silently
	skipping one would hand a new hire no card and nobody would notice until the
	kiosk rejects them.
	"""
	selectors = [bool(codes), bool(from_code or to_code), bool(from_joining or to_joining)]
	if sum(selectors) != 1:
		frappe.throw(_("Provide exactly one of: a code list, a code range, or a joining-date range"))

	# Permission gate — same doctype permission as the single-card endpoint;
	# frappe.get_list below additionally applies row-level user permissions.
	if not frappe.has_permission("Employee", "read"):
		raise frappe.PermissionError(_("Not permitted to read Employees"))

	filters = {"status": "Active"}
	if codes:
		wanted = [c for c in re.split(r"[\s,;]+", codes) if c]
		filters["name"] = ["in", wanted]
	elif from_code or to_code:
		if not (from_code and to_code):
			frappe.throw(_("Both from_code and to_code are required for a code range"))
		filters["name"] = ["between", [from_code.strip(), to_code.strip()]]
	else:
		if not (from_joining and to_joining):
			frappe.throw(_("Both from_joining and to_joining are required for a date range"))
		filters["date_of_joining"] = ["between", [from_joining, to_joining]]

	names = [r.name for r in frappe.get_list("Employee", filters=filters,
	                                         fields=["name"], order_by="name",
	                                         limit_page_length=MAX_BATCH_CARDS + 1)]
	if codes:
		missing = sorted(set(wanted) - set(names))
		if missing:
			frappe.throw(_("Not found or not Active: {0}").format(", ".join(missing)))
	if not names:
		frappe.throw(_("No Active employees match"))
	if len(names) > MAX_BATCH_CARDS:
		frappe.throw(_("Range matches more than {0} employees — narrow it and print in parts")
		             .format(MAX_BATCH_CARDS))

	cards = [_card_data(frappe.get_doc("Employee", n)) for n in names]
	pdf = render_employee_card_sheet_form(cards)

	frappe.local.response.filename = "ID-cards-%s-x%d.pdf" % (names[0], len(names))
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "download"
