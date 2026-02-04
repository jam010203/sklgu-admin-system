# Disbursement Voucher Quick Start Guide

## ✅ System Ready to Use

The disbursement voucher system is now fully implemented with automatic voucher numbering.

## Quick Reference

### DV Number Format
```
YYYY-MM-###
2026-02-001  ← February 2026, 1st voucher
2026-02-002  ← February 2026, 2nd voucher
2026-03-001  ← March 2026, 1st voucher (resets)
```

## How to Create a Voucher

### Step 1: Navigate
Go to `http://localhost:5000/disbursement-voucher`

### Step 2: Create
Click **"Create New Voucher"** button

### Step 3: Fill Form
| Field | What to Enter | Example |
|---|---|---|
| Payee | Person/Entity receiving payment | John Doe |
| Address | Complete address | 123 Main Street |
| TIN | Tax Identification Number | 12345678 |
| Province | Province | Camarines Sur |
| City/Municipality | Department/Office | Finance Department |
| Date | Voucher date | 2026-02-15 |
| Fund | Fund designation | General Fund |
| Particulars | Description of disbursement | Office supplies purchase |
| Amount | Total amount | 5000.00 |

### Step 4: Save
Click **"Save Voucher"** button

**Result:** DV number automatically generates! (e.g., 2026-02-001)

## How to View Vouchers

1. Click **"View All Vouchers"**
2. See list of all your vouchers
3. Click any voucher to load for editing or printing
4. Click **"Print Voucher"** to print/save as PDF

## How to Edit Voucher

1. Click **"View All Vouchers"**
2. Click voucher you want to edit
3. Form loads with data
4. Make changes
5. Click **"Save Voucher"** to update

## How to Delete Voucher

1. Click **"View All Vouchers"**
2. Find voucher in list
3. Click red **Delete** button
4. Confirm deletion
5. Voucher removed from system

**Note:** Only draft vouchers can be deleted

## Automatic Features

### ✨ Auto-Incrementing
- Each voucher gets next number automatically
- No manual numbering needed
- System tracks sequence per month

### ✨ Monthly Reset
- New month = Sequence resets to 001
- Keeps vouchers organized by month
- Easy to find vouchers by month

### ✨ Unique Numbers
- No duplicate DV numbers possible
- System prevents duplicates
- Professional documentation

## API Endpoints (For Developers)

### Create Voucher
```bash
POST /api/disbursement-voucher
Content-Type: application/json

{
  "payee": "John Doe",
  "address": "123 Main St",
  "tin": "12345678",
  "province": "Camarines Sur",
  "responsibility_center": "Finance",
  "fund_cluster": "General Fund",
  "voucher_date": "2026-02-15",
  "particulars": "Office supplies",
  "amount_due": 5000.00
}
```

### Get All Vouchers
```bash
GET /api/disbursement-vouchers
```

### Get Specific Voucher
```bash
GET /api/disbursement-voucher/{id}
```

### Update Voucher
```bash
PUT /api/disbursement-voucher/{id}
Content-Type: application/json

{ "payee": "New Name", ... }
```

### Delete Voucher
```bash
DELETE /api/disbursement-voucher/{id}
```

## Example DV Numbers

### February 2026
```
2026-02-001  ← 1st
2026-02-002  ← 2nd
2026-02-003  ← 3rd
...
2026-02-050  ← 50th
```

### March 2026
```
2026-03-001  ← 1st (resets)
2026-03-002  ← 2nd
```

## Common Tasks

### Print a Voucher
1. Create or load voucher
2. Click **"Print Voucher"**
3. Preview appears
4. Click print or save as PDF

### Find Vouchers by Month
1. Click **"View All Vouchers"**
2. Look for DV numbers starting with desired month
3. 2026-02-### = February vouchers
4. 2026-03-### = March vouchers

### Export Voucher Data
1. Click **"View All Vouchers"**
2. Click desired voucher
3. Right-click in form area
4. Choose "Save As" or "Print to File"

## Troubleshooting

### DV Number Not Showing
- Click "Save Voucher" again
- Check browser console (F12) for errors
- Refresh page

### Cannot Delete Voucher
- Only draft vouchers can be deleted
- If voucher is submitted, cannot delete
- Contact administrator

### Form Data Lost
- Make sure to click "Save Voucher"
- Use "View All Vouchers" to load saved data
- Browser refresh clears unsaved data

## Technical Details

### Database Field: dv_number
- **Type:** String (50 characters)
- **Unique:** Yes (prevents duplicates)
- **Format:** YYYY-MM-###
- **Generated:** Automatic
- **Editable:** No (read-only)

### Sequence Counter
- Counts per user, per month
- Resets each month
- Maximum 999 vouchers per month per user
- Supports leap years and all months

### Storage
- Stored in `dis_voucher` table
- Indexed for fast lookup
- Backed up with database

## System Requirements

- ✓ Flask server running
- ✓ SQLite database
- ✓ User logged in
- ✓ Modern web browser
- ✓ JavaScript enabled

## Support

For issues or questions:
1. Check VOUCHER_IMPLEMENTATION.md for technical details
2. Check VOUCHER_NUMBERING_SYSTEM.md for format details
3. Review this Quick Start Guide
4. Contact system administrator

---

**Version:** 1.0  
**Last Updated:** February 2, 2026  
**Status:** ✅ Ready to Use
