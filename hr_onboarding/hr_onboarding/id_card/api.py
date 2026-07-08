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
	doc = frappe.get_doc("Employee", employee)

	card = EmployeeCardData(
		employee_id=doc.name,
		employee_name=doc.employee_name or "",
		department=doc.department or "",
		grade=doc.grade or "",
		designation=doc.designation or "",
		date_of_joining=str(doc.date_of_joining or ""),
		photo_data_uri=_photo_data_uri(doc.image),
	)

	return render_employee_card_sheet_form([card])
