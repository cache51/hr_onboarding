# HR Onboarding - Frappe Custom Fields App

Custom fields for the HR Onboarding Flutter mobile app integration with ERPNext,
plus **Employee ID card printing** — a "Print ID Card" button on the Employee form
(see [Employee ID Card](#employee-id-card)).

## Installation

### System prerequisites (once per bench host)

The ID card renders with **WeasyPrint**, which needs Pango and friends at the OS
level (these are system libraries, NOT Python packages). Run once, as root, on the
bench host:

```bash
sudo apt-get update
sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
                        libharfbuzz0b libgdk-pixbuf-2.0-0 libcairo2
# Vietnamese text needs a Unicode font — DejaVu is usually already present:
fc-list | grep -qi dejavu || sudo apt-get install -y fonts-dejavu
```

> Only skip this if you won't use the ID card. Without Pango, install/build still
> succeed, but generating a card fails with `cannot load library 'libpango-1.0.so'`.

### Fresh Install

```bash
# Get the app from GitHub (latest release)
bench get-app https://github.com/cache51/hr_onboarding.git --branch v1.6.0

# Install to your site (also installs the Python deps: segno, weasyprint)
bench --site YOUR_SITE install-app hr_onboarding

# Build the "Print ID Card" button assets, migrate, restart
bench build --app hr_onboarding
bench --site YOUR_SITE migrate
bench restart
```

### Update Existing Installation

```bash
# Pull the new version. If already tracking the repo:
cd apps/hr_onboarding && git fetch && git checkout v1.6.0 && cd ../..
# Install/refresh the Python deps (segno, weasyprint)
bench setup requirements hr_onboarding

# Build assets, migrate, restart
bench build --app hr_onboarding
bench --site YOUR_SITE migrate
bench restart
```

## Employee ID Card

Adds a **Print ID Card** button to the Employee form (shown to *HR User*, *HR
Manager*, *System Manager*). It renders the HR-approved worker badge —
**THẺ CÔNG NHÂN VIÊN** (crown logo, company header, QR = MSNV, photo, name,
department, position, join date) — and downloads it as `ID-<MSNV>.pdf`. The QR
encodes the MSNV (`Employee.name`), so the same card doubles as the kiosk/gate badge.

| Piece | Location |
|-------|----------|
| Renderer (WeasyPrint, vendored from the leave app) | `hr_onboarding/id_card/employee_card.py` |
| Whitelisted endpoint (HR-gated) | `hr_onboarding.hr_onboarding.id_card.api.print_employee_id_card` |
| Button (wired via `doctype_js`) | `hr_onboarding/public/js/employee_id_card.js` |
| Python deps | `segno`, `weasyprint` (`pyproject.toml`) |
| System deps | Pango et al. — see [System prerequisites](#system-prerequisites-once-per-bench-host) |

Uses the employee's photo (`Employee.image`) when present, else a blank "ẢNH 3×4" box.

## Custom Fields Created

| # | Field Name | Type | Label | Insert After | Tab |
|---|------------|------|-------|--------------|-----|
| 1 | `custom_national_id_num` | Data | National ID Number | `passport_number` | Personal Details |
| 2 | `custom_ethnicity` | Data | Ethnicity | `family_background` | Personal Details |
| 3 | `custom_cccd_front_image` | Attach Image | CCCD Front Image | `valid_upto` | Personal Details |
| 4 | `custom_cccd_back_image` | Attach Image | CCCD Back Image | `place_of_issue` | Personal Details |
| 5 | `custom_shirt_size` | Select | Shirt Size | `health_details` | Personal Details |
| 6 | `custom_referral_person_name` | Data | Referral Person Name | `candidate_source` | Joining |

## Existing Fields (No Custom Fields Needed)

### Employee Doctype
- `candidate_source` (Link) - Joining tab - recruitment source
- `custom_hometown` / `native_place` - origin/hometown
- `health_insurance_provider` (Link) - insurance location
- `social_insurance_no` (Data) - social insurance ID
- `valid_upto` (Date) - CCCD expiry date
- `working_years` (Data) - years of experience
- `nation` (Data) - nationality

### Employee Education Child Table
- `level` (Select) - education level with custom options:
  - Secondary School (THCS)
  - High School (THPT)
  - College & Above
- `maj_opt_subj` (Text) - major/subject
- `school_univ` (Small Text) - school name

### External Work History Child Table
- `company_name` (Data) - previous workplace (NOT `company`)
- `designation` (Data) - job title
- `contact` (Data) - department
- `total_experience` (Data) - years of experience

## Field Positioning Rules

Custom fields use `insert_after` to specify position:
- Fields in **Personal Details** tab: passport_number, family_background, valid_upto, place_of_issue, health_details
- Fields in **Joining** tab: candidate_source (after probation_time_to)

## Complete Flutter to ERPNext Field Mapping

### Basic Info (Page A)
| Flutter | ERPNext | Status |
|---------|---------|--------|
| fullName | employee_name | Standard |
| gender | gender | Standard |
| dateOfBirth | date_of_birth | Standard |
| cccdNumber | passport_number | Standard |
| cccdIssueDate | date_of_issue | Standard |
| cccdExpiryDate | valid_upto | Standard |
| cccdIssuePlace | place_of_issue | Standard |
| phoneNumber | cell_number | Standard |
| bankName | bank_name | Standard |
| bankAccountNumber | bank_ac_no | Standard |
| nationalIdNum | custom_national_id_num | **Custom (create)** |
| ethnicity | custom_ethnicity | **Custom (create)** |
| cccdFrontImagePath | custom_cccd_front_image | **Custom (create)** |
| cccdBackImagePath | custom_cccd_back_image | **Custom (create)** |

### Address (Page B)
| Flutter | ERPNext | Status |
|---------|---------|--------|
| origin | custom_hometown / native_place | Exists |
| permanent | permanent_address | Standard |
| currentType | current_accommodation_type | Standard |
| currentAddress | current_address | Standard |

### Education (Page C - Employee Education table)
| Flutter | ERPNext | Status |
|---------|---------|--------|
| educationLevel | level | Standard |
| schoolName | school_univ | Standard |
| major | maj_opt_subj | Standard |

### Work History (Page C - External Work History table)
| Flutter | ERPNext | Status |
|---------|---------|--------|
| jobTitle | designation | Standard |
| department | contact | Standard |
| yearsOfExperience | total_experience | Standard |
| previousWorkplace | company_name | Standard |

### Insurance (Page D)
| Flutter | ERPNext | Status |
|---------|---------|--------|
| socialInsuranceNumber | social_insurance_no | Exists |
| insuranceRegistrationLocation | health_insurance_provider | Exists |

### Personal (Page E)
| Flutter | ERPNext | Status |
|---------|---------|--------|
| maritalStatus | marital_status | Standard |
| shirtSize | custom_shirt_size | **Custom (create)** |

### Recruitment (Page F)
| Flutter | ERPNext | Status |
|---------|---------|--------|
| recruitmentSource | candidate_source | Exists |
| referralPersonName | custom_referral_person_name | **Custom (create)** |

### Emergency Contact (Page G)
| Flutter | ERPNext | Status |
|---------|---------|--------|
| emergencyContactName | person_to_be_contacted | Standard |
| emergencyContactRelationship | relation | Standard |
| emergencyContactPhone | emergency_phone_number | Standard |

## Verification

After installation, verify custom fields exist:

```sql
SELECT fieldname, fieldtype, label
FROM `tabCustom Field`
WHERE dt = 'Employee'
AND fieldname LIKE 'custom_%'
ORDER BY fieldname;
```

## References
- [Frappe Custom Fields](https://docs.frappe.io/framework/user/en/api/document)
- [ERPNext Employee Doctype](https://docs.frappe.io/erpnext/introduction)
