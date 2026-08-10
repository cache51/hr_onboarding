// "Print ID Cards" on the Employee LIST view — batch printing (HR request
// 10 Aug 2026, item 5). One dialog, three ways to choose who:
//   - the rows ticked in the list (pre-filled),
//   - a typed MSNV list,
//   - an MSNV range from → to,
//   - a joining-date range.
// Renders server-side (api.print_employee_id_cards) as one 9-up A4 PDF.
//
// HRMS may also define listview settings for Employee — extend, never replace.
(function () {
    frappe.listview_settings = frappe.listview_settings || {};
    const existing = frappe.listview_settings["Employee"] || {};
    const prev_onload = existing.onload;

    existing.onload = function (listview) {
        if (prev_onload) { prev_onload(listview); }
        if (!(frappe.user.has_role("HR User") || frappe.user.has_role("HR Manager")
              || frappe.user.has_role("System Manager"))) { return; }

        listview.page.add_inner_button(__("Print ID Cards"), () => {
            const checked = (listview.get_checked_items() || []).map(r => r.name);
            const d = new frappe.ui.Dialog({
                title: __("Print ID Cards"),
                fields: [
                    { fieldtype: "Small Text", fieldname: "codes",
                      label: __("Employee codes (comma / space separated)"),
                      default: checked.join(", "),
                      description: __("Leave the other fields empty when using a list") },
                    { fieldtype: "Section Break", label: __("… or a code range") },
                    { fieldtype: "Data", fieldname: "from_code", label: __("From code (e.g. R00002)") },
                    { fieldtype: "Column Break" },
                    { fieldtype: "Data", fieldname: "to_code", label: __("To code (e.g. R00050)") },
                    { fieldtype: "Section Break", label: __("… or a joining-date range") },
                    { fieldtype: "Date", fieldname: "from_joining", label: __("Joined from") },
                    { fieldtype: "Column Break" },
                    { fieldtype: "Date", fieldname: "to_joining", label: __("Joined to") },
                ],
                primary_action_label: __("Print"),
                primary_action(values) {
                    const chosen = [!!values.codes,
                                    !!(values.from_code || values.to_code),
                                    !!(values.from_joining || values.to_joining)]
                                   .filter(Boolean).length;
                    if (chosen !== 1) {
                        frappe.msgprint(__("Fill exactly one selector: a code list, a code range, or a date range"));
                        return;
                    }
                    const params = new URLSearchParams();
                    for (const k of ["codes", "from_code", "to_code", "from_joining", "to_joining"]) {
                        if (values[k]) { params.set(k, values[k]); }
                    }
                    window.open("/api/method/hr_onboarding.hr_onboarding.id_card.api.print_employee_id_cards?"
                                + params.toString(), "_blank");
                    d.hide();
                },
            });
            d.show();
        });
    };
    frappe.listview_settings["Employee"] = existing;
})();
