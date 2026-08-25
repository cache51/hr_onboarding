# -*- coding: utf-8 -*-
"""Bulk import of employee photos, matched to employees by MSNV filename.

HR asked to upload many photos at once instead of one at a time (ERP HR module
sheet, 19/8). The Employee ``image`` field is an Attach Image and takes a single
file, so this fills the gap: point it at a folder or a ZIP whose files are named
after the employee code and it sets ``Employee.image`` for each one.

Matching is on the filename stem only -- ``R00496.jpg`` -> employee ``R00496``.
Nothing is inferred from employee names: Vietnamese names collide constantly
(dozens of NGUYEN THI ...), and silently attaching a photo to the wrong person
is worse than not importing it. Anything that does not match is reported, never
guessed at.

Photos are stored as PRIVATE files by default. They are employee PII, and files
under /files/ are readable by anyone who knows the URL. The ID card renderer
reads the bytes through the File doc, so private works there.
"""
from __future__ import unicode_literals

import io
import os
import zipfile

import frappe
from frappe import _

# Extensions we accept. Anything else in the folder/archive is reported as
# skipped rather than silently ignored.
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")

# Guard against a stray huge file being attached to an employee record.
MAX_IMAGE_BYTES = 10 * 1024 * 1024


class PhotoImportResult(object):
	"""Tally of one import run, including everything that did NOT import."""

	def __init__(self, dry_run=False):
		self.dry_run = dry_run
		self.imported = []        # (employee, filename)
		self.skipped_existing = []  # (employee, filename) - already had a photo
		self.unmatched = []       # (filename, reason) - no such employee, etc.
		self.errors = []          # (filename, message)

	def as_dict(self):
		return {
			"dry_run": self.dry_run,
			"imported": self.imported,
			"skipped_existing": self.skipped_existing,
			"unmatched": self.unmatched,
			"errors": self.errors,
			"counts": {
				"imported": len(self.imported),
				"skipped_existing": len(self.skipped_existing),
				"unmatched": len(self.unmatched),
				"errors": len(self.errors),
			},
		}

	def summary(self):
		c = self.as_dict()["counts"]
		prefix = "DRY RUN - nothing written. " if self.dry_run else ""
		return (
			"{0}{1} imported, {2} skipped (already had a photo), "
			"{3} unmatched, {4} errors".format(
				prefix, c["imported"], c["skipped_existing"],
				c["unmatched"], c["errors"]
			)
		)


def _employee_code(filename):
	"""Employee code from a filename, or None if it is not an image we take."""
	base = os.path.basename(filename)
	stem, ext = os.path.splitext(base)
	if ext.lower() not in IMAGE_EXTENSIONS:
		return None
	# HR exports often carry trailing markers like "R00496 (1).jpg" or
	# "R00496_2.jpg"; take the leading token so those still land correctly.
	stem = stem.strip().split()[0] if stem.strip() else ""
	stem = stem.split("_")[0]
	return stem.upper() or None


def _attach(employee, filename, content, is_private=1):
	"""Attach `content` to `employee` and point Employee.image at it."""
	file_doc = frappe.get_doc({
		"doctype": "File",
		"file_name": os.path.basename(filename),
		"attached_to_doctype": "Employee",
		"attached_to_name": employee,
		"attached_to_field": "image",
		"is_private": is_private,
		"content": content,
	})
	file_doc.save(ignore_permissions=True)
	frappe.db.set_value("Employee", employee, "image", file_doc.file_url,
	                    update_modified=False)
	return file_doc.file_url


def import_photos(items, dry_run=False, overwrite=False, is_private=1):
	"""Import an iterable of ``(filename, bytes)`` pairs.

	Both the folder and ZIP entry points funnel through here so they behave
	identically. Each file is handled independently: one bad image cannot
	abort the rest of the run.
	"""
	result = PhotoImportResult(dry_run=dry_run)

	for filename, content in items:
		code = _employee_code(filename)
		if not code:
			result.unmatched.append((filename, "not a .jpg/.jpeg/.png file"))
			continue

		if not content:
			result.errors.append((filename, "file is empty"))
			continue

		if len(content) > MAX_IMAGE_BYTES:
			result.errors.append(
				(filename, "larger than {0} MB".format(MAX_IMAGE_BYTES // (1024 * 1024)))
			)
			continue

		if not frappe.db.exists("Employee", code):
			result.unmatched.append((filename, "no employee '{0}'".format(code)))
			continue

		existing = frappe.db.get_value("Employee", code, "image")
		if existing and not overwrite:
			result.skipped_existing.append((code, filename))
			continue

		if dry_run:
			result.imported.append((code, filename))
			continue

		try:
			_attach(code, filename, content, is_private=is_private)
			result.imported.append((code, filename))
		except Exception as exc:
			# Keep going: a single unreadable image should not cost the whole run.
			result.errors.append((filename, frappe.utils.cstr(exc)))
			frappe.log_error(
				title="Photo import failed for {0}".format(code),
				message=frappe.get_traceback(),
			)

	if not dry_run:
		frappe.db.commit()

	return result


def _iter_folder(folder):
	for name in sorted(os.listdir(folder)):
		path = os.path.join(folder, name)
		if not os.path.isfile(path):
			continue
		with open(path, "rb") as fh:
			yield name, fh.read()


def _iter_zip(zip_bytes):
	with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
		for info in archive.infolist():
			if info.is_dir():
				continue
			# Zips made on macOS carry __MACOSX/._name resource forks; they are
			# not real images and would otherwise show up as unmatched noise.
			name = info.filename
			if "__MACOSX" in name or os.path.basename(name).startswith("._"):
				continue
			yield os.path.basename(name), archive.read(info)


def import_from_folder(folder, dry_run=False, overwrite=False, is_private=1):
	"""Import every image in `folder`. Intended for `bench execute`."""
	if not os.path.isdir(folder):
		frappe.throw(_("Not a folder: {0}").format(folder))
	result = import_photos(_iter_folder(folder), dry_run=dry_run,
	                       overwrite=overwrite, is_private=is_private)
	print(result.summary())
	for code, name in result.imported:
		print("  imported  {0}  <- {1}".format(code, name))
	for code, name in result.skipped_existing:
		print("  skipped   {0}  <- {1} (already has a photo)".format(code, name))
	for name, reason in result.unmatched:
		print("  UNMATCHED {0}  ({1})".format(name, reason))
	for name, msg in result.errors:
		print("  ERROR     {0}  ({1})".format(name, msg))
	return result.as_dict()


def import_from_zip_bytes(zip_bytes, dry_run=False, overwrite=False, is_private=1):
	"""Import every image inside a ZIP. Used by the desk page."""
	try:
		items = list(_iter_zip(zip_bytes))
	except zipfile.BadZipFile:
		frappe.throw(_("That file is not a valid ZIP archive."))
	return import_photos(items, dry_run=dry_run, overwrite=overwrite,
	                     is_private=is_private)
