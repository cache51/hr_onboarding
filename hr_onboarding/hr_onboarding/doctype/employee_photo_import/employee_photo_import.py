# -*- coding: utf-8 -*-
"""Desk front-end for the bulk employee photo importer.

Each record is one import run, kept so HR can see what happened rather than
having the outcome vanish with a toast message.
"""
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document

from hr_onboarding.hr_onboarding.photo_import.importer import import_from_zip_bytes


class EmployeePhotoImport(Document):
	pass


def _archive_bytes(file_url):
	"""Read the uploaded archive back out of the File store."""
	name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not name:
		frappe.throw(_("Could not find the uploaded file. Re-attach the archive."))
	return frappe.get_doc("File", name).get_content()


def _format_log(data):
	lines = []
	for code, fname in data["imported"]:
		lines.append("imported   {0}  <- {1}".format(code, fname))
	for code, fname in data["skipped_existing"]:
		lines.append("skipped    {0}  <- {1}  (already has a photo)".format(code, fname))
	for fname, reason in data["unmatched"]:
		lines.append("UNMATCHED  {0}  ({1})".format(fname, reason))
	for fname, msg in data["errors"]:
		lines.append("ERROR      {0}  ({1})".format(fname, msg))
	return "\n".join(lines) or "Nothing to report."


@frappe.whitelist()
def run_import(docname):
	"""Run the import for one Employee Photo Import record."""
	doc = frappe.get_doc("Employee Photo Import", docname)

	if not frappe.has_permission("Employee", "write"):
		raise frappe.PermissionError(_("Not permitted to update Employee records"))
	if not doc.photo_archive:
		frappe.throw(_("Attach a .zip of photos first."))

	result = import_from_zip_bytes(
		_archive_bytes(doc.photo_archive),
		dry_run=bool(doc.dry_run),
		overwrite=bool(doc.overwrite_existing),
		is_private=1 if doc.keep_private else 0,
	)
	data = result.as_dict()

	doc.db_set("summary", result.summary(), update_modified=False)
	doc.db_set("result_log", _format_log(data), update_modified=False)
	frappe.db.commit()

	return data
