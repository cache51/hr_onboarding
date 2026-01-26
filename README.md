# HR Onboarding - Frappe Custom Fields App

Custom fields for the HR Onboarding Flutter mobile app integration with ERPNext.

## Installation

### Fresh Install

```bash
# Get the app from GitHub (specific version)
bench get-app https://github.com/cache51/hr_onboarding.git --branch v1.0.2

# Install to your site
bench --site YOUR_SITE install-app hr_onboarding

# Run migrations
bench --site YOUR_SITE migrate
```

### Update Existing Installation

```bash
# Update the app
bench update --apps hr_onboarding

# Run migrations
bench --site YOUR_SITE migrate
```

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
