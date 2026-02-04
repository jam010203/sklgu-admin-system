# DV Number Format - Visual Guide

## The Format

```
┌────────────────────────────────┐
│ YYYY - MM - ###                │
│ 2026 - 02 - 001                │
└────────────────────────────────┘
  ↓     ↓     ↓
  Year  Mo.   Seq.
```

## Component Breakdown

### YYYY (Year)
- **4 digits**
- Example: 2026
- Changes every year
- Range: 2000-9999

### MM (Month)
- **2 digits with zero-padding**
- Examples: 01, 02, 03... 12
- Leading zero for months 1-9
- Changes every month

### ### (Sequence)
- **3 digits with zero-padding**
- Examples: 001, 002, 003... 999
- Leading zeros for sequences 1-99
- Resets to 001 every month

---

## Real Examples

### February 2026 Sequence
```
Voucher 1:  2026-02-001
Voucher 2:  2026-02-002
Voucher 3:  2026-02-003
...
Voucher 9:  2026-02-009
Voucher 10: 2026-02-010
Voucher 99: 2026-02-099
Voucher 100: 2026-02-100
Voucher 999: 2026-02-999 (max)
```

### Across Months in 2026
```
January:   2026-01-001, 2026-01-002, ... 2026-01-XXX
February:  2026-02-001, 2026-02-002, ... 2026-02-XXX
March:     2026-03-001, 2026-03-002, ... 2026-03-XXX
April:     2026-04-001, 2026-04-002, ... 2026-04-XXX
...
December:  2026-12-001, 2026-12-002, ... 2026-12-XXX
```

### Monthly Pattern
```
2026-01-050 ← January, 50th voucher
2026-02-001 ← February, RESETS to 1st!
2026-02-050 ← February, 50th voucher
2026-03-001 ← March, RESETS to 1st!
```

---

## Visual Timeline

```
January 2026
│
├─ 2026-01-001 (Jan 1st voucher)
├─ 2026-01-002 (Jan 2nd voucher)
├─ 2026-01-003 (Jan 3rd voucher)
└─ ... (more January vouchers)
│
February 2026 ← SEQUENCE RESETS!
│
├─ 2026-02-001 (Feb 1st voucher) ← Back to 001!
├─ 2026-02-002 (Feb 2nd voucher)
├─ 2026-02-003 (Feb 3rd voucher)
└─ ... (more February vouchers)
│
March 2026 ← SEQUENCE RESETS!
│
├─ 2026-03-001 (Mar 1st voucher) ← Back to 001!
├─ 2026-03-002 (Mar 2nd voucher)
└─ ... (more March vouchers)
```

---

## Key Rules

### ✓ Correct Formats
```
2026-01-001  ✓
2026-02-010  ✓
2026-03-100  ✓
2026-12-999  ✓
2025-06-050  ✓
2027-08-005  ✓
```

### ✗ Incorrect Formats
```
26-02-001         ✗ (year needs 4 digits)
2026-2-001        ✗ (month needs 2 digits)
2026-02-1         ✗ (sequence needs 3 digits)
2026-02-001-A     ✗ (no letters allowed)
2026/02/001       ✗ (must use hyphens)
```

---

## Zero-Padding Examples

### Month Zero-Padding
```
January   = 01  (not 1)
February  = 02  (not 2)
March     = 03  (not 3)
...
September = 09  (not 9)
October   = 10  (stays 10)
November  = 11  (stays 11)
December  = 12  (stays 12)
```

### Sequence Zero-Padding
```
1st       = 001  (not 1 or 01)
2nd       = 002  (not 2 or 02)
...
9th       = 009  (not 9 or 09)
10th      = 010  (not 10 alone)
99th      = 099  (not 99 alone)
100th     = 100  (stays 100)
```

---

## Examples by Month

### All Months in 2026

```
JANUARY (01)      FEBRUARY (02)     MARCH (03)        APRIL (04)
2026-01-001       2026-02-001       2026-03-001       2026-04-001
2026-01-002       2026-02-002       2026-03-002       2026-04-002
2026-01-003       2026-02-003       2026-03-003       2026-04-003

MAY (05)          JUNE (06)         JULY (07)         AUGUST (08)
2026-05-001       2026-06-001       2026-07-001       2026-08-001
2026-05-002       2026-06-002       2026-07-002       2026-08-002
2026-05-003       2026-06-003       2026-07-003       2026-08-003

SEPTEMBER (09)    OCTOBER (10)      NOVEMBER (11)     DECEMBER (12)
2026-09-001       2026-10-001       2026-11-001       2026-12-001
2026-09-002       2026-10-002       2026-11-002       2026-12-002
2026-09-003       2026-10-003       2026-11-003       2026-12-003
```

---

## Quick Reference Card

### Format Template
```
┌─────────────────────────────┐
│ YYYY - MM - ###             │
│ EEEE - EE - EEE             │
│ 2026 - 02 - 001             │
│ Year   M    Seq             │
└─────────────────────────────┘
```

### Breakdown Table
| Component | Format | Example | Notes |
|-----------|--------|---------|-------|
| Year | 4 digits | 2026 | Current year |
| Separator | Hyphen | - | Dash character |
| Month | 2 digits | 02 | Zero-padded |
| Separator | Hyphen | - | Dash character |
| Sequence | 3 digits | 001 | Zero-padded |

### Limits
| Component | Minimum | Maximum | Notes |
|-----------|---------|---------|-------|
| Year | 2000 | 9999 | Any 4-digit year |
| Month | 01 | 12 | Jan to Dec |
| Sequence | 001 | 999 | Per month limit |

---

## Month Reference Table

| Month | Code | Example DV |
|-------|------|-----------|
| January | 01 | 2026-01-001 |
| February | 02 | 2026-02-001 |
| March | 03 | 2026-03-001 |
| April | 04 | 2026-04-001 |
| May | 05 | 2026-05-001 |
| June | 06 | 2026-06-001 |
| July | 07 | 2026-07-001 |
| August | 08 | 2026-08-001 |
| September | 09 | 2026-09-001 |
| October | 10 | 2026-10-001 |
| November | 11 | 2026-11-001 |
| December | 12 | 2026-12-001 |

---

## Common Questions

### Q: Why does month start at 01 instead of 00?
**A:** Standard calendar convention. January = 01, December = 12.

### Q: Why zero-pad the sequence to 3 digits?
**A:** Allows up to 999 vouchers per month, maintains consistent sorting, professional appearance.

### Q: Can the sequence go beyond 999?
**A:** No, the system limits it to 999 per month. Create new month for more vouchers.

### Q: What happens at year 2027?
**A:** Year changes to 2027, month still resets. Example: 2027-01-001

### Q: Can two users have the same DV number?
**A:** Yes, each user has their own counter per month. Both can have 2026-02-001.

### Q: What if a voucher is created on Jan 31st?
**A:** It gets 2026-01-### regardless of date. Month is when created, not when dated.

---

## Visual DV Number Anatomy

```
D V   N U M B E R
2 0 2 6 - 0 2 - 0 0 1

Breaking it down:

2 0 2 6      = Year (2026)
     -       = Separator (hyphen)
       0 2   = Month (February)
          -  = Separator (hyphen)
            0 0 1 = Sequence (1st of month)


Position:  1 2 3 4 5 6 7 8 9 10 11
Character: 2 0 2 6 - 0 2 -  0  0  1

```

---

## Practical Examples

### User Creates 3 Vouchers in February
```
1st save  → DV Number: 2026-02-001
2nd save  → DV Number: 2026-02-002
3rd save  → DV Number: 2026-02-003
```

### Same User Creates Voucher in March
```
1st save (of March) → DV Number: 2026-03-001  ← Resets!
```

### Different User Saves in February
```
Can still get 2026-02-001  ← Different user, same number is OK
```

---

## Regex Pattern (For Validation)

```regex
^\d{4}-\d{2}-\d{3}$

Breakdown:
^      = Start of string
\d{4}  = Exactly 4 digits (year)
-      = Literal hyphen
\d{2}  = Exactly 2 digits (month)
-      = Literal hyphen
\d{3}  = Exactly 3 digits (sequence)
$      = End of string
```

---

## Test Your Knowledge

### Match these to DV format:

1. `2026-02-001` → Valid? **YES** ✓
2. `2026-2-001` → Valid? **NO** ✗ (month needs 2 digits)
3. `2026-02-01` → Valid? **NO** ✗ (sequence needs 3 digits)
4. `26-02-001` → Valid? **NO** ✗ (year needs 4 digits)
5. `2026-02-100` → Valid? **YES** ✓
6. `2026-13-001` → Valid? **NO** ✗ (month can't be 13)
7. `2026-02-000` → Valid? **NO** ✗ (sequence starts at 001)
8. `2026-02-1000` → Valid? **NO** ✗ (sequence max is 999)

---

**Format Verified:** ✅ YYYY-MM-### (e.g., 2026-02-001)  
**Status:** Ready for Production  
**Last Updated:** February 2, 2026
