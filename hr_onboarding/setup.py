import frappe


def after_install():
    """Create custom fields after app installation"""
    create_custom_fields()
    frappe.db.commit()


def create_custom_fields():
    """Create all required custom fields for Employee doctype"""
    custom_fields = {
        "Employee": [
            {
                "fieldname": "custom_national_id_num",
                "fieldtype": "Data",
                "label": "National ID Number",
                "insert_after": "passport_number",
                "translatable": 0
            },
            {
                "fieldname": "custom_ethnicity",
                "fieldtype": "Data",
                "label": "Ethnicity",
                "insert_after": "family_background",
                "translatable": 0
            },
            {
                "fieldname": "custom_cccd_front_image",
                "fieldtype": "Attach Image",
                "label": "CCCD Front Image",
                "insert_after": "valid_upto"
            },
            {
                "fieldname": "custom_cccd_back_image",
                "fieldtype": "Attach Image",
                "label": "CCCD Back Image",
                "insert_after": "place_of_issue"
            },
            {
                "fieldname": "custom_shirt_size",
                "fieldtype": "Select",
                "label": "Shirt Size",
                "options": "XS\nS\nM\nL\nXL\nXXL\nXXXL",
                "insert_after": "health_details"
            },
            {
                "fieldname": "custom_referral_person_name",
                "fieldtype": "Data",
                "label": "Referral Person Name",
                "insert_after": "candidate_source",
                "translatable": 0
            }
        ]
    }

    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields as _create
    _create(custom_fields)
