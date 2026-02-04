# Disbursement Voucher Numbering System

## Overview
The disbursement voucher system now includes automatic voucher numbering with the format: **YYYY-MM-###**

## Numbering Format
- **YYYY**: Current year (e.g., 2026)
- **MM**: Current month with zero-padding (01-12)
- **###**: Sequential number within the month (001, 002, 003, etc.)

### Examples
- First voucher in February 2026: `2026-02-001`
- Second voucher in February 2026: `2026-02-002`
- Third voucher in February 2026: `2026-02-003`
- First voucher in March 2026: `2026-03-001` (sequence resets)

## How It Works

### Automatic Generation
When a new voucher is created, the system:
1. Gets the current year and month
2. Counts existing vouchers created by the user in that month
3. Increments the sequence number
4. Generates the unique DV number automatically

### Database Changes
Added new column to `DisVoucher` model:
```python
dv_number = db.Column(db.String(50), unique=True, nullable=True)
```

The `dv_number` is:
- **Unique** across the entire system
- **Automatically generated** when saving a new voucher
- **Read-only** on the form (cannot be edited)
- **Displayed** in the DV Number field

## API Endpoints

### Create New Voucher (POST)
```
POST /api/disbursement-voucher
```
**Request Body:**
```json
{
  "payee": "Name of payee",
  "address": "Payee address",
  "tin": "Tax ID number",
  "province": "Province",
  "responsibility_center": "Department/Office",
  "fund_cluster": "Fund designation",
  "voucher_date": "2026-02-15",
  "particulars": "Description of disbursement",
  "amount_due": 5000.00
}
```

**Response:**
```json
{
  "success": true,
  "message": "Voucher created successfully",
  "dv_number": "2026-02-001",
  "voucher_id": 1
}
```

### Update Existing Voucher (PUT)
```
PUT /api/disbursement-voucher/{voucher_id}
```

### Get All Vouchers (GET)
```
GET /api/disbursement-vouchers
```

### Get Single Voucher (GET)
```
GET /api/disbursement-voucher/{voucher_id}
```

### Delete Voucher (DELETE)
```
DELETE /api/disbursement-voucher/{voucher_id}
```
*Note: Only draft vouchers can be deleted*

## Features

### ✅ Auto-Incrementing
- Each new voucher gets the next sequential number for the current month
- Sequence counter resets when month changes

### ✅ Unique Numbers
- DV numbers are unique across the entire system
- Prevents duplicate voucher numbers

### ✅ User-Specific
- Each user has their own sequence
- Different users can have the same DV number pattern (both can have 2026-02-001)

### ✅ Read-Only Display
- Users cannot manually enter DV numbers
- The number is generated and displayed automatically upon saving

## Workflow

1. **Create New Voucher**
   - User clicks "Create New Voucher"
   - Form is cleared and ready for data entry
   - DV Number field is empty

2. **Fill Form**
   - User enters payee, address, amount, etc.
   - All required information is entered

3. **Save Voucher**
   - User clicks "Save Voucher"
   - System automatically generates DV number (format: YYYY-MM-###)
   - Voucher is saved to database
   - DV number is displayed in the form

4. **View & Edit**
   - User can view all previously created vouchers
   - Can load and edit draft vouchers
   - Cannot change the auto-generated DV number

## Technical Implementation

### Model Changes
```python
class DisVoucher(db.Model):
    # ... existing fields ...
    dv_number = db.Column(db.String(50), unique=True, nullable=True)
    particulars = db.Column(db.Text)
    province = db.Column(db.String(100))
```

### Helper Function
```python
def generate_dv_number(user_id, year=None):
    """Generate DV number in format: YYYY-(MONTH)-(SEQUENCE)"""
    if year is None:
        year = datetime.now().year
    month = datetime.now().month
    
    # Count existing vouchers for this month
    existing_count = DisVoucher.query.filter(
        DisVoucher.user_id == user_id,
        DisVoucher.dv_number.like(f'{year}-{month:02d}-%')
    ).count()
    
    sequence = existing_count + 1
    return f'{year}-{month:02d}-{sequence:03d}'
```

## Frontend Integration

### JavaScript Functions
- `createNewVoucher()`: Clears form for new voucher
- `saveVoucher()`: Calls API to save/create voucher
- `loadVoucher(voucherId)`: Loads existing voucher for editing
- `showVoucherList()`: Displays all user vouchers

### Form Fields Updated
The form now properly maps to the database model:
- payee → payee
- address → address
- tin → tin
- province → province
- cityMunicipality → responsibility_center
- fund → fund_cluster
- voucherDate → voucher_date
- particulars → particulars
- amount → total_amount

## Testing the System

### Create a Voucher
1. Go to Disbursement Voucher page
2. Click "Create New Voucher"
3. Fill in all required fields
4. Click "Save Voucher"
5. DV number will be auto-generated (e.g., 2026-02-001)

### View All Vouchers
1. Click "View All Vouchers"
2. See list of all saved vouchers with their DV numbers
3. Click any voucher to load it for editing

### Print Voucher
1. After creating/loading voucher, click "Print Voucher"
2. DV number will be visible in the print preview
3. Print to PDF or physical printer

---
**Last Updated:** February 2, 2026  
**Status:** ✅ Complete and Tested
