app_name = "hr_onboarding"
app_title = "HR Onboarding"
app_publisher = "RGM"
app_description = "Custom fields for HR onboarding mobile app"
app_email = "admin@rgm.vn"
app_license = "MIT"
required_apps = ["frappe", "erpnext"]

# Client scripts injected into doctype forms
doctype_js = {
    "Employee": "public/js/employee_id_card.js"
}

# Fixtures - auto-install custom fields when app is installed
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["fieldname", "in", [
                "custom_national_id_num",
                "custom_ethnicity",
                "custom_cccd_front_image",
                "custom_cccd_back_image",
                "custom_shirt_size",
                "custom_referral_person_name"
            ]]
        ]
    },
    {
        "dt": "Property Setter",
        "filters": [
            ["doc_type", "=", "Employee Education"],
            ["field_name", "=", "level"],
            ["property", "=", "options"]
        ]
    }
]

# After install hook to create custom fields
after_install = "hr_onboarding.setup.after_install"

# After migrate hook to ensure education level options are set
after_migrate = ["hr_onboarding.setup.set_education_level_options"]
