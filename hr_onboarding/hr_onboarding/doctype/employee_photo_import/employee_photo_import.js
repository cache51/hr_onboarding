// Import run UI. The document must be saved first so the archive is in the
// File store and the run has somewhere to record its result.
frappe.ui.form.on('Employee Photo Import', {
    refresh: function (frm) {
        if (frm.doc.__islocal) { return; }

        frm.add_custom_button(__('Run Import'), () => {
            if (!frm.doc.photo_archive) {
                frappe.msgprint(__('Attach a .zip of photos first.'));
                return;
            }
            const proceed = () => {
                frappe.dom.freeze(__('Importing photos…'));
                frappe.call({
                    method: 'hr_onboarding.hr_onboarding.doctype.employee_photo_import.employee_photo_import.run_import',
                    args: { docname: frm.doc.name },
                }).then((r) => {
                    frappe.dom.unfreeze();
                    const c = (r.message || {}).counts || {};
                    frappe.msgprint({
                        title: frm.doc.dry_run ? __('Dry run complete') : __('Import complete'),
                        indicator: c.errors ? 'orange' : 'green',
                        message: __('{0} imported, {1} skipped, {2} unmatched, {3} errors',
                            [c.imported || 0, c.skipped_existing || 0,
                             c.unmatched || 0, c.errors || 0]),
                    });
                    frm.reload_doc();
                }).catch(() => frappe.dom.unfreeze());
            };

            // Writing is the irreversible half; a dry run needs no confirmation.
            if (frm.doc.dry_run) {
                proceed();
            } else {
                frappe.confirm(
                    frm.doc.overwrite_existing
                        ? __('This will set employee photos and REPLACE any that already exist. Continue?')
                        : __('This will set photos for employees that do not have one. Continue?'),
                    proceed
                );
            }
        }).addClass(frm.doc.dry_run ? '' : 'btn-primary');
    },
});
