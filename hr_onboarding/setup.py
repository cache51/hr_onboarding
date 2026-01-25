import frappe


def after_install():
    """Create custom fields after app installation"""
    create_custom_fields()
    set_education_level_options()
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


def set_education_level_options():
    """Set education level options for Employee Education child table"""
    education_levels = "\nSecondary School (THCS)\nHigh School (THPT)\nCollege & Above"
    ps_name = "Employee Education-level-options"

    # Check if Property Setter already exists
    if frappe.db.exists("Property Setter", ps_name):
        # Update existing Property Setter
        frappe.db.set_value("Property Setter", ps_name, "value", education_levels)
    else:
        # Create new Property Setter
        from frappe.custom.doctype.property_setter.property_setter import make_property_setter
        make_property_setter(
            doctype="Employee Education",
            fieldname="level",
            property="options",
            value=education_levels,
            property_type="Text",
            for_doctype=False
        )
