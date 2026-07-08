// Adds a "Print ID Card" button to the Employee form for HR roles.
// Renders the HR-approved card server-side (hr_onboarding.id_card.api) and
// downloads it as ID-<MSNV>.pdf.
frappe.ui.form.on("Employee", {
    refresh: function(frm) {
        if (frm.doc.__islocal) { return; }
        if (!(frappe.user.has_role("HR User") || frappe.user.has_role("HR Manager")
              || frappe.user.has_role("System Manager"))) { return; }
        frm.add_custom_button(__('Print ID Card'), () => {
            const url = '/api/method/hr_onboarding.hr_onboarding.id_card.api.print_employee_id_card'
                      + '?employee=' + encodeURIComponent(frm.doc.name);
            window.open(url, '_blank');
        });
    }
});
