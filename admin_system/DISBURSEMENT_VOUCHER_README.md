# Disbursement Voucher System

## Overview
The Disbursement Voucher system provides a standardized, fillable, and printable voucher template that all users must use for recording disbursement transactions. All voucher records are automatically saved to the database for tracking and reporting purposes.

## Features

### ✅ Standardized Template
- Official government disbursement voucher format
- Matches barangay/SK accounting requirements
- All users must use the same template for consistency

### ✅ Fillable Form
- **Header Section:**
  - DV Number (Auto-generated)
  - Responsibility
  - City/Municipality
  - Fund
  
- **Payee Information:**
  - Payee Name
  - Province
  - Address
  - TIN
  
- **Particulars:**
  - Detailed description area
  - Amount field
  
- **Three Certification Sections:**
  - A. Certified as to Existence of Appropriation for Obligation (SK Kagawad Monitoring Officer)
  - B. Certified as to Availability of Funds (SK Treasurer)
  - C. Certified as to Validity and Approved for Payment (SK Chairperson)
  
- **Received Payment:**
  - Check Number
  - Bank Name
  - OR Number
  - Date
  - Signature
  
- **Accounting Entries:**
  - Account Title
  - Account Code
  - Debit/Credit amounts
  - Multiple rows supported
  
- **Approval Signatures:**
  - Barangay Bookkeeper
  - City/Municipal Accountant

### ✅ Printable
- Optimized print layout
- Clean formatting for official documentation
- Removes buttons and controls when printing
- Professional appearance suitable for official records

### ✅ Database Recording
- All vouchers automatically saved to database
- Track voucher status (draft, submitted, approved, completed)
- View all previous vouchers
- Edit and update existing vouchers
- Delete vouchers when needed
- Search and filter capabilities

## How to Use

### Creating a New Voucher

1. **Access the System**
   - Log in to your user account
   - Click on "📑 Disbursement Voucher" in the sidebar menu

2. **Fill Out the Form**
   
   **Header Information:**
   - Enter Responsibility (department/office)
   - Enter City/Municipality
   - Enter Fund designation
   - DV Number is auto-generated upon saving

   **Payee Information:**
   - Enter Payee name (person/entity receiving payment)
   - Enter Province
   - Enter complete Address
   - Enter TIN (Tax Identification Number)

   **Particulars:**
   - Enter detailed description of the disbursement
   - Enter the total Amount

   **Section A - Certified as to Existence of Appropriation:**
   - Enter name of SK Kagawad Monitoring Officer
   - Select date

   **Section B - Certified as to Availability of Funds:**
   - Enter name of SK Treasurer
   - Select date

   **Section C - Certified for Payment:**
   - Enter name of SK Chairperson
   - Select date

   **Section D - Received Payment:**
   - Enter Check Number
   - Enter Bank Name
   - Enter OR (Official Receipt) Number
   - Select Payment Date
   - Enter signature of payee

   **Section E - Accounting Entries:**
   - Enter Account title
   - Enter Account Code
   - Enter Debit amount
   - Enter Credit amount
   - Click "Add Row" to add more entries as needed

   **Final Approval:**
   - Enter name of Barangay Bookkeeper (Prepared by)
   - Enter name of City/Municipal Accountant (Approved by)
   - Select dates

3. **Save the Voucher**
   - Click "Save Voucher" button
   - System generates a unique DV number (format: DV-YYYY-####)
   - Confirmation message appears
   - Voucher is saved to database

### Viewing All Vouchers

1. Click "View All Vouchers" button
2. List of all your vouchers displays with:
   - DV Number
   - Entity Name
   - Payee
   - Amount
   - Status
   - Creation Date
3. Click on any voucher to load and edit it

### Editing an Existing Voucher

1. Click "View All Vouchers"
2. Click on the voucher you want to edit
3. Form populates with existing data
4. Make your changes
5. Click "Save Voucher" to update

### Printing a Voucher

1. Fill out the voucher form (or load an existing one)
2. Click "Print Voucher" or use Ctrl+P (Cmd+P on Mac)
3. Print preview shows clean, professional format
4. Select printer and print settings
5. Print the voucher

### Deleting a Voucher

1. Click "View All Vouchers"
2. Find the voucher to delete
3. Click the red trash icon
4. Confirm deletion
5. Voucher is permanently removed from database

## Voucher Status

Vouchers can have the following statuses:

- **Draft** (Yellow): Voucher is being prepared
- **Submitted** (Blue): Voucher submitted for approval
- **Approved** (Green): Voucher has been approved
- **Completed** (Gray): Voucher processing is complete

## Data Recorded in Database

The system automatically records:
- All header information
- Payment mode details
- Payee information
- All particulars line items
- Total amount due
- All accounting entries
- Certification selections
- All signature information
- Receipt of payment details
- Voucher status
- Creation and update timestamps

## Access Control

- Only logged-in users can access the disbursement voucher system
- Each user can only view and edit their own vouchers
- All actions are tracked with user ID
- Admins can view all vouchers (if admin functionality is added)

## Technical Details

### Database Model
- **Table:** `disbursement_voucher`
- **Primary Key:** Auto-incrementing ID
- **Unique Constraint:** DV Number
- **Foreign Key:** User ID

### API Endpoints
- `GET /disbursement-voucher` - Voucher page
- `GET /api/disbursement-vouchers` - List all user vouchers
- `GET /api/disbursement-voucher/<id>` - Get specific voucher
- `POST /api/disbursement-voucher` - Create new voucher
- `PUT /api/disbursement-voucher/<id>` - Update voucher
- `DELETE /api/disbursement-voucher/<id>` - Delete voucher

### Security
- Session-based authentication required
- User can only access their own vouchers
- CSRF protection enabled
- Input validation on all fields

## Best Practices

1. **Save Frequently** - Click save after filling major sections
2. **Use Draft Status** - Keep vouchers in draft until ready for submission
3. **Double-Check Amounts** - Verify all amounts before printing
4. **Complete All Fields** - Fill in all required information for official records
5. **Print After Approval** - Only print vouchers that are approved
6. **Keep Digital Records** - Database maintains permanent record of all vouchers

## Support

For questions or issues with the Disbursement Voucher system:
- Contact your system administrator
- Refer to this documentation
- Check the user manual for general system navigation

---

**System Version:** 1.0  
**Last Updated:** February 2, 2026  
**Maintained by:** SKLGU Admin System Team
