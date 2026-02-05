"""
SKLGU Admin System - Main Application
Handles admin authentication, user management, and system operations
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import secrets
import csv
from io import TextIOWrapper
from dotenv import load_dotenv

# Load environment variables from admin_system/.env if present
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)
# Use persistent secret key from environment or generate once (not recommended for production)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Get absolute path for database
db_path = os.path.join(basedir, 'database', 'sklgu_admin.db')

# Ensure database directory exists for local SQLite fallback
os.makedirs(os.path.join(basedir, 'database'), exist_ok=True)

# Use persistent database if provided (recommended for production)
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', os.path.join(basedir, 'uploads'))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def normalize_upload_filename(filename):
    """Normalize uploaded file names to a safe basename for serving."""
    if not filename:
        return None
    normalized = filename.replace('\\', '/').strip()
    for prefix in ('uploads/', 'admin_system/uploads/', 'static/uploads/'):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            break
    normalized = os.path.basename(normalized)
    return normalized or None

db = SQLAlchemy(app)

# ==================== Database Models ====================

class Admin(db.Model):
    """Admin user model - only admins can create accounts"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    """Regular user account"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    current_password = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_password_change = db.Column(db.DateTime)
    account_status = db.Column(db.String(50), default='pending')


class UserProfile(db.Model):
    """User profile information"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(200))
    phone_no = db.Column(db.String(20))
    email = db.Column(db.String(120))
    position = db.Column(db.String(100))
    barangay = db.Column(db.String(100))
    municipality = db.Column(db.String(100))
    complete_address = db.Column(db.Text)
    birthdate = db.Column(db.Date)
    profile_picture = db.Column(db.String(300))
    brgy_sk_logo = db.Column(db.String(300))
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AccountApproval(db.Model):
    """Account approval tracking"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    approved_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
    approval_date = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Announcement(db.Model):
    """System announcements"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    announcement_image = db.Column(db.String(300))
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnnouncementComment(db.Model):
    """Comments on announcements"""
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AnnouncementView(db.Model):
    """Track announcement views"""
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)


class AnnouncementFile(db.Model):
    """Files attached to announcements"""
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(300), nullable=False)
    file_path = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AnnouncementLike(db.Model):
    """Likes on announcements"""
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AnnouncementNotification(db.Model):
    """Notifications for announcement interactions"""
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # 'like' or 'comment'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DisVoucher(db.Model):
    """Disbursement Voucher"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dv_number = db.Column(db.String(50), unique=True, nullable=True)
    barangay = db.Column(db.String(200))
    payee = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    tin = db.Column(db.String(50))
    province = db.Column(db.String(100))
    responsibility_center = db.Column(db.String(200))
    fund_cluster = db.Column(db.String(100))
    voucher_date = db.Column(db.Date)
    particulars = db.Column(db.Text)
    status = db.Column(db.String(50), default='draft')
    total_amount = db.Column(db.Float, default=0)
    # Check/Payment Info
    check_number = db.Column(db.String(50))
    bank_name = db.Column(db.String(200))
    or_number = db.Column(db.String(50))
    payment_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DisVoucherLine(db.Model):
    """Disbursement Voucher Line Items"""
    id = db.Column(db.Integer, primary_key=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('dis_voucher.id'), nullable=False)
    account_code = db.Column(db.String(50))
    description = db.Column(db.Text)
    amount = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DisbursementReport(db.Model):
    """Disbursement Report"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    report_date = db.Column(db.Date)
    total_amount = db.Column(db.Float, default=0)
    file_path = db.Column(db.String(300))
    status = db.Column(db.String(50), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Minute(db.Model):
    """Minutes of Meetings"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    meeting_date = db.Column(db.Date)
    file_path = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Resolution(db.Model):
    """Resolutions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resolution_number = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    date_passed = db.Column(db.Date)
    file_path = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InventoryItem(db.Model):
    """Inventory items"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Float)
    unit_price = db.Column(db.Float)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LiquidationReport(db.Model):
    """Liquidation report header"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lr_no = db.Column(db.String(100))
    report_date = db.Column(db.Date)
    barangay = db.Column(db.String(200))
    municipality = db.Column(db.String(200))
    province = db.Column(db.String(200))
    cash_advance_amount = db.Column(db.Float, default=0)
    cash_advance_dv_no = db.Column(db.String(100))
    cash_advance_date = db.Column(db.Date)
    refunded_amount = db.Column(db.Float, default=0)
    refunded_or_no = db.Column(db.String(100))
    refunded_date = db.Column(db.Date)
    amount_reimbursed = db.Column(db.Float, default=0)
    certified_a_name = db.Column(db.String(200))
    certified_b_name = db.Column(db.String(200))
    certified_c_name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LiquidationItem(db.Model):
    """Liquidation report line items"""
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('liquidation_report.id'), nullable=False)
    particulars = db.Column(db.Text)
    amount = db.Column(db.Float, default=0)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AnnualProcurementPlan(db.Model):
    """Annual Procurement Plan (APP) header"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    app_no = db.Column(db.String(100))
    barangay = db.Column(db.String(200))
    municipality = db.Column(db.String(200))
    province = db.Column(db.String(200))
    calendar_year = db.Column(db.Integer)
    office_name = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AppProcurementItem(db.Model):
    """Annual Procurement Plan line items"""
    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.Integer, db.ForeignKey('annual_procurement_plan.id'), nullable=False)
    description = db.Column(db.Text)
    unit_cost = db.Column(db.Float, default=0)
    quantity = db.Column(db.Float, default=0)
    unit = db.Column(db.String(50))
    total_cost = db.Column(db.Float, default=0)
    q1_qty = db.Column(db.Float, default=0)
    q1_amt = db.Column(db.Float, default=0)
    q2_qty = db.Column(db.Float, default=0)
    q2_amt = db.Column(db.Float, default=0)
    q3_qty = db.Column(db.Float, default=0)
    q3_amt = db.Column(db.Float, default=0)
    q4_qty = db.Column(db.Float, default=0)
    q4_amt = db.Column(db.Float, default=0)
    row_type = db.Column(db.String(50), default='DATA')  # 'DATA', 'LABEL', or 'TOTAL'
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PasswordChangeRequest(db.Model):
    """Password change requests pending admin approval"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    new_password_hash = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='pending')
    approved_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
    approval_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PasswordHistory(db.Model):
    """Password change history"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    password_plain = db.Column(db.String(200))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by = db.Column(db.String(50), default='user')


class UserCreationLog(db.Model):
    """Log of user account creation"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by_admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    user_email = db.Column(db.String(120), nullable=False)
    admin_email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BudgetFYTemplate(db.Model):
    """Budget for F.Y template"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    fiscal_year = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BudgetFYRow(db.Model):
    """Budget for F.Y row items"""
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('budget_fy_template.id'), nullable=False)
    section = db.Column(db.String(200))
    program = db.Column(db.String(200))
    project_activities = db.Column(db.Text)
    account_code = db.Column(db.String(50))
    duration = db.Column(db.String(100))
    mooe = db.Column(db.Float, default=0)
    co = db.Column(db.Float, default=0)
    amount = db.Column(db.Float, default=0)
    row_type = db.Column(db.String(50), default='DATA')  # 'DATA' or 'TOTAL'
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BudgetProject(db.Model):
    """Individual budget projects from Budget F.Y. templates"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('budget_fy_template.id'), nullable=False)
    budget_row_id = db.Column(db.Integer, db.ForeignKey('budget_fy_row.id'), nullable=False)
    project_name = db.Column(db.Text, nullable=False)  # from project_activities
    fiscal_year = db.Column(db.String(50))
    total_budget = db.Column(db.Float, default=0)  # original amount
    disbursed_amount = db.Column(db.Float, default=0)  # total disbursed
    remaining_balance = db.Column(db.Float, default=0)  # computed field
    account_code = db.Column(db.String(50))
    section = db.Column(db.String(200))
    program = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VoucherBudgetAllocation(db.Model):
    """Track which budget projects are allocated to which vouchers"""
    id = db.Column(db.Integer, primary_key=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('dis_voucher.id'), nullable=False)
    budget_project_id = db.Column(db.Integer, db.ForeignKey('budget_project.id'), nullable=False)
    allocated_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PurchaseRequest(db.Model):
    """Purchase Request"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pr_number = db.Column(db.String(50), unique=True)
    barangay = db.Column(db.String(200))
    municipality = db.Column(db.String(200))
    province = db.Column(db.String(200))
    pr_date = db.Column(db.Date)
    purpose = db.Column(db.Text)
    total_amount = db.Column(db.Float, default=0)
    requested_by = db.Column(db.String(200))
    requested_by_position = db.Column(db.String(200))
    requested_date = db.Column(db.Date)
    approved_by = db.Column(db.String(200))
    approved_by_position = db.Column(db.String(200))
    approved_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PurchaseRequestItem(db.Model):
    """Purchase Request Line Items"""
    id = db.Column(db.Integer, primary_key=True)
    pr_id = db.Column(db.Integer, db.ForeignKey('purchase_request.id'), nullable=False)
    item_no = db.Column(db.Integer)
    quantity = db.Column(db.Float, default=0)
    unit_of_measurement = db.Column(db.String(50))
    item_description = db.Column(db.Text)
    estimated_unit_cost = db.Column(db.Float, default=0)
    estimated_amount = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Canvass(db.Model):
    """Canvass (Request for Price Quotation)"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pr_number = db.Column(db.String(50))
    canvass_date = db.Column(db.Date)
    fod = db.Column(db.Text)
    delivery_days = db.Column(db.Integer)
    total_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default='draft')
    canvassed_by = db.Column(db.String(200))
    canvassed_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CanvassItem(db.Model):
    """Canvass Line Items"""
    id = db.Column(db.Integer, primary_key=True)
    canvass_id = db.Column(db.Integer, db.ForeignKey('canvass.id'), nullable=False)
    item_no = db.Column(db.Integer)
    quantity = db.Column(db.Float, default=0)
    unit = db.Column(db.String(50))
    articles = db.Column(db.Text)
    unit_price = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==================== Database Initialization ====================
# Initialize database tables on app startup
with app.app_context():
    try:
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Always ensure default admin exists (important for ephemeral storage)
        admin_count = Admin.query.count()
        print(f"Current admin count: {admin_count}")
        
        if admin_count == 0:
            default_admin = Admin(
                email='admin@sklgu.gov.ph',
                password_hash=generate_password_hash('admin123'),
                is_super_admin=True
            )
            db.session.add(default_admin)
            db.session.commit()
            print("✓ Default admin created: admin@sklgu.gov.ph / admin123")
        else:
            # List existing admins
            admins = Admin.query.all()
            print(f"✓ Existing admins: {[admin.email for admin in admins]}")
    except Exception as e:
        print(f"✗ Database initialization error: {e}")
        import traceback
        traceback.print_exc()


# ==================== Routes ====================

@app.route('/')
def index():
    """Home page - redirect to login/dashboard based on session"""
    if 'user_id' in session:
        return redirect(url_for('user_dashboard'))
    elif 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User/Admin login page"""
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json(silent=True) or {}
                email = data.get('email', '').strip()
                password = data.get('password', '')
            else:
                email = request.form.get('email', '').strip()
                password = request.form.get('password', '')

            if not email or not password:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Email and password are required'}), 400
                return render_template('login.html', error='Email and password are required')

            # Try admin login first
            admin = Admin.query.filter_by(email=email).first()
            if admin and check_password_hash(admin.password_hash, password):
                session['admin_id'] = admin.id
                session['admin_email'] = admin.email
                if request.is_json:
                    return jsonify({'success': True, 'redirect': url_for('admin_dashboard')}), 200
                return redirect(url_for('admin_dashboard'))
            
            # Try user login
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['user_email'] = user.email
                
                # Check if user profile is completed
                profile = UserProfile.query.filter_by(user_id=user.id).first()
                if not profile or not profile.is_completed:
                    # Redirect to pre-dashboard to complete profile
                    if request.is_json:
                        return jsonify({'success': True, 'redirect': url_for('user_pre_dashboard')}), 200
                    return redirect(url_for('user_pre_dashboard'))
                
                if request.is_json:
                    return jsonify({'success': True, 'redirect': url_for('user_dashboard')}), 200
                return redirect(url_for('user_dashboard'))
            
            # Invalid credentials
            if request.is_json:
                return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            return render_template('login.html', error='Invalid email or password')
        
        except Exception as e:
            print(f"Login error: {e}")
            if request.is_json:
                return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
            return render_template('login.html', error='An error occurred during login')

    return render_template('login.html')


@app.route('/user-dashboard')
def user_dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('user-dashboard.html')


@app.route('/user-pre-dashboard')
def user_pre_dashboard():
    """User pre-dashboard - for completing profile"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if profile is already completed
    profile = UserProfile.query.filter_by(user_id=session['user_id']).first()
    if profile and profile.is_completed:
        return redirect(url_for('user_dashboard'))
    
    return render_template('user-pre-dashboard.html')


@app.route('/admin-dashboard')
def admin_dashboard():
    """Admin dashboard"""
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    return render_template('main-dashboard.html')


@app.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'success': True})


@app.route('/complete-profile', methods=['POST'])
def complete_profile():
    """Complete user profile after login"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        user_id = session['user_id']
        
        # Get or create user profile
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
        
        # Update profile fields
        profile.full_name = request.form.get('full_name')
        profile.phone_no = request.form.get('phone_no')
        profile.email = request.form.get('email')
        profile.position = request.form.get('position')
        profile.barangay = request.form.get('barangay')
        profile.municipality = request.form.get('municipality')
        profile.complete_address = request.form.get('complete_address')
        birthdate_value = request.form.get('birthdate')
        if birthdate_value:
            try:
                profile.birthdate = datetime.fromisoformat(birthdate_value).date()
            except (ValueError, TypeError):
                profile.birthdate = None
        else:
            profile.birthdate = None
        
        # Handle file uploads
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename and '.' in file.filename:
                try:
                    # Read file and encode as base64 for database storage
                    file.seek(0)
                    file_data = file.read()
                    file_ext = file.filename.rsplit('.', 1)[1].lower()
                    
                    # Save to uploads folder as well for backward compatibility
                    filename = secure_filename(f"profile_{user_id}_{secrets.token_hex(8)}.{file_ext}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # Make sure uploads folder exists
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    with open(file_path, 'wb') as f:
                        f.write(file_data)
                    
                    profile.profile_picture = filename
                except Exception as e:
                    print(f"Error saving profile picture: {e}")
        
        if 'brgy_logo' in request.files:
            file = request.files['brgy_logo']
            if file and file.filename and '.' in file.filename:
                try:
                    # Read file and encode as base64 for database storage
                    file.seek(0)
                    file_data = file.read()
                    file_ext = file.filename.rsplit('.', 1)[1].lower()
                    
                    # Save to uploads folder as well for backward compatibility
                    filename = secure_filename(f"logo_{user_id}_{secrets.token_hex(8)}.{file_ext}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # Make sure uploads folder exists
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    with open(file_path, 'wb') as f:
                        f.write(file_data)
                    
                    profile.brgy_sk_logo = filename
                except Exception as e:
                    print(f"Error saving brgy logo: {e}")
        
        # Mark profile as completed
        profile.is_completed = True
        profile.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Profile completed successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/create-user', methods=['POST'])
def create_user():
    """Create new user account (admin only)"""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        data = request.get_json(silent=True) or {}
        email = data.get('email')
        password = data.get('password')
        
        # Validate input
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'User with this email already exists'}), 400
        
        # Create new user
        new_user = User(
            email=email,
            password_hash=generate_password_hash(password),
            account_status='active'
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Log user creation in database
        admin = Admin.query.get(session['admin_id'])
        admin_email = admin.email if admin else 'Unknown'
        
        creation_log = UserCreationLog(
            user_id=new_user.id,
            created_by_admin_id=session['admin_id'],
            user_email=new_user.email,
            admin_email=admin_email
        )
        db.session.add(creation_log)
        db.session.commit()
        
        # Also print to console for immediate visibility
        print(f"[ADMIN LOG] User created: {email} (ID: {new_user.id}) by Admin: {admin_email} (ID: {session['admin_id']}) at {datetime.utcnow().isoformat()}")
        
        return jsonify({
            'success': True, 
            'message': 'User account created successfully',
            'user_id': new_user.id,
            'email': new_user.email
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500



# ==================== User Management Routes ====================

@app.route('/get-profile')
def get_profile():
    """Get current user profile"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    user = User.query.get(session['user_id'])
    profile = UserProfile.query.filter_by(user_id=session['user_id']).first()

    if not user:
        return jsonify({'success': False}), 404

    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': profile.full_name if profile else '',
            'position': profile.position if profile else '',
            'barangay': profile.barangay if profile else '',
            'municipality': profile.municipality if profile else '',
            'birthdate': profile.birthdate.isoformat() if profile and profile.birthdate else '',
            'profile_picture': normalize_upload_filename(profile.profile_picture) if profile else None,
            'is_completed': profile.is_completed if profile else False
        }
    })


@app.route('/update-profile', methods=['POST'])
def update_profile():
    """Update user profile"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        user_id = session['user_id']
        profile = UserProfile.query.filter_by(user_id=user_id).first()

        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)

        profile.full_name = request.form.get('full_name', profile.full_name)
        profile.position = request.form.get('position', profile.position)
        profile.barangay = request.form.get('barangay', profile.barangay)
        profile.municipality = request.form.get('municipality', profile.municipality)

        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                # Extract original file extension
                file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
                filename = secure_filename(f"profile_{user_id}_{secrets.token_hex(8)}.{file_ext}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Delete old profile picture if exists
                if profile.profile_picture:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], profile.profile_picture)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass
                profile.profile_picture = filename

        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/get-member-leaderboard')
def get_member_leaderboard():
    """Get leaderboard of all members with budget status"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    members = UserProfile.query.all()
    
    result = []
    for member in members:
        template_count = BudgetFYTemplate.query.filter_by(user_id=member.user_id).count()
        budget_status = 'Has Budget' if template_count > 0 else 'No Budget Data'
        
        result.append({
            'id': member.user_id,
            'full_name': member.full_name or 'Unknown',
            'position': member.position,
            'barangay': member.barangay,
            'municipality': member.municipality,
            'profile_picture': normalize_upload_filename(member.profile_picture),
            'barangay_budget_status': budget_status
        })
    
    return jsonify({'success': True, 'members': result})


# ==================== Announcement Routes ====================

@app.route('/get-announcements')
def get_announcements():
    """Get announcements for user/admin"""
    if 'user_id' not in session and 'admin_id' not in session:
        return jsonify({'success': False}), 401

    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()

    return jsonify({
        'success': True,
        'announcements': [{
            'id': a.id,
            'title': a.title,
            'content': a.content,
            'image': a.announcement_image,
            'posted_at': a.created_at.isoformat(),
            'created_at': a.created_at.isoformat(),
            'view_count': a.view_count,
            'comment_count': AnnouncementComment.query.filter_by(announcement_id=a.id).count(),
            'created_by': a.user_id
        } for a in announcements]
    })


@app.route('/get-announcement-comments/<int:announcement_id>')
def get_announcement_comments(announcement_id):
    """Get comments for an announcement"""
    comments = AnnouncementComment.query.filter_by(announcement_id=announcement_id).all()
    return jsonify({
        'success': True,
        'comments': [{
            'id': c.id,
            'comment': c.comment,
            'user_id': c.user_id,
            'created_at': c.created_at.isoformat()
        } for c in comments]
    })


@app.route('/get-user-announcements')
def get_user_announcements():
    """Get announcements with comments for user announcements page"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    result = []
    for ann in announcements:
        comments = AnnouncementComment.query.filter_by(announcement_id=ann.id).all()
        comment_list = []
        for comment in comments:
            comment_user = User.query.get(comment.user_id)
            comment_list.append({
                'id': comment.id,
                'comment': comment.comment,
                'user_email': comment_user.email if comment_user else 'Unknown',
                'posted_at': comment.created_at.isoformat()
            })

        files = AnnouncementFile.query.filter_by(announcement_id=ann.id).order_by(AnnouncementFile.created_at.asc()).all()
        file_list = []
        for file_item in files:
            file_user = User.query.get(file_item.user_id)
            file_list.append({
                'id': file_item.id,
                'filename': file_item.filename,
                'file_path': file_item.file_path,
                'user_email': file_user.email if file_user else 'Unknown',
                'uploaded_at': file_item.created_at.isoformat()
            })

        # Get admin/poster info - check if posted by admin
        admin = Admin.query.get(ann.user_id)
        if admin:
            # Posted by admin
            poster_name = f"Admin ({admin.email})"
            poster_profile_pic = None
        else:
            # Posted by regular user (fallback)
            poster = User.query.get(ann.user_id)
            poster_profile = UserProfile.query.filter_by(user_id=ann.user_id).first() if poster else None
            poster_name = poster_profile.full_name if poster_profile and poster_profile.full_name else (poster.email if poster else 'Unknown')
            poster_profile_pic = normalize_upload_filename(poster_profile.profile_picture) if poster_profile else None
        
        # Get likes count and check if current user liked
        likes_count = AnnouncementLike.query.filter_by(announcement_id=ann.id).count()
        user_liked = AnnouncementLike.query.filter_by(announcement_id=ann.id, user_id=session['user_id']).first() is not None
        
        result.append({
            'id': ann.id,
            'title': ann.title,
            'content': ann.content,
            'posted_at': ann.created_at.isoformat(),
            'announcement_image': ann.announcement_image,
            'poster_name': poster_name,
            'poster_profile_pic': poster_profile_pic,
            'likes_count': likes_count,
            'user_liked': user_liked,
            'comments': comment_list,
            'files': file_list
        })

    return jsonify({'success': True, 'announcements': result})


@app.route('/add-announcement-comment/<int:announcement_id>', methods=['POST'])
def add_announcement_comment(announcement_id):
    """Add comment to announcement"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    # Verify announcement exists
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'success': False, 'message': 'Announcement not found'}), 404

    data = request.get_json(silent=True) or {}
    comment_text = data.get('comment', '').strip()

    if not comment_text:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400

    try:
        comment = AnnouncementComment(
            announcement_id=announcement_id,
            user_id=session['user_id'],
            comment=comment_text
        )
        db.session.add(comment)
        
        # Create notification for admin
        notification = AnnouncementNotification(
            announcement_id=announcement_id,
            user_id=session['user_id'],
            notification_type='comment'
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Comment added'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/add-announcement-comment', methods=['POST'])
def add_announcement_comment_body():
    """Add comment to announcement (body-based)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.get_json(silent=True) or {}
    announcement_id = data.get('announcement_id')
    comment_text = data.get('comment', '').strip()

    if not announcement_id:
        return jsonify({'success': False, 'message': 'Announcement ID required'}), 400
    if not comment_text:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400

    # Verify announcement exists
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'success': False, 'message': 'Announcement not found'}), 404

    try:
        comment = AnnouncementComment(
            announcement_id=announcement_id,
            user_id=session['user_id'],
            comment=comment_text
        )
        db.session.add(comment)
        
        # Create notification for admin
        notification = AnnouncementNotification(
            announcement_id=announcement_id,
            user_id=session['user_id'],
            notification_type='comment'
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Comment added'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/toggle-announcement-like/<int:announcement_id>', methods=['POST'])
def toggle_announcement_like(announcement_id):
    """Like or unlike an announcement"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        announcement = Announcement.query.get(announcement_id)
        if not announcement:
            return jsonify({'success': False, 'message': 'Announcement not found'}), 404

        existing_like = AnnouncementLike.query.filter_by(
            announcement_id=announcement_id,
            user_id=session['user_id']
        ).first()

        if existing_like:
            # Unlike
            db.session.delete(existing_like)
            # Remove notification if exists
            AnnouncementNotification.query.filter_by(
                announcement_id=announcement_id,
                user_id=session['user_id'],
                notification_type='like'
            ).delete()
            db.session.commit()
            likes_count = AnnouncementLike.query.filter_by(announcement_id=announcement_id).count()
            return jsonify({'success': True, 'liked': False, 'likes_count': likes_count})
        else:
            # Like
            new_like = AnnouncementLike(
                announcement_id=announcement_id,
                user_id=session['user_id']
            )
            db.session.add(new_like)
            
            # Create notification for admin
            notification = AnnouncementNotification(
                announcement_id=announcement_id,
                user_id=session['user_id'],
                notification_type='like'
            )
            db.session.add(notification)
            db.session.commit()
            likes_count = AnnouncementLike.query.filter_by(announcement_id=announcement_id).count()
            return jsonify({'success': True, 'liked': True, 'likes_count': likes_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/upload-announcement-file/<int:announcement_id>', methods=['POST'])
def upload_announcement_file(announcement_id):
    """Upload a file attachment for an announcement"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        announcement = Announcement.query.get(announcement_id)
        if not announcement:
            return jsonify({'success': False, 'message': 'Announcement not found'}), 404

        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400

        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        safe_name = secure_filename(file.filename)
        if not safe_name:
            return jsonify({'success': False, 'message': 'Invalid filename'}), 400

        file_ext = safe_name.rsplit('.', 1)[1].lower() if '.' in safe_name else 'dat'
        stored_name = secure_filename(
            f"announcement_{announcement_id}_{session['user_id']}_{secrets.token_hex(8)}.{file_ext}"
        )
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], stored_name))

        record = AnnouncementFile(
            announcement_id=announcement_id,
            user_id=session['user_id'],
            filename=safe_name,
            file_path=stored_name
        )
        db.session.add(record)
        db.session.commit()

        return jsonify({'success': True, 'message': 'File uploaded'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/post-announcement', methods=['POST'])
def post_announcement():
    """Create new announcement (admin only)"""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        data = request.get_json(silent=True) or {}
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()

        if not title or not content:
            return jsonify({'success': False, 'message': 'Title and content are required'}), 400

        # Use admin_id as user_id for announcements
        announcement = Announcement(
            user_id=session['admin_id'],
            title=title,
            content=content
        )
        db.session.add(announcement)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Announcement posted successfully', 'id': announcement.id})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/edit-announcement/<int:announcement_id>', methods=['POST'])
def edit_announcement(announcement_id):
    """Edit announcement (admin only)"""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        announcement = Announcement.query.get_or_404(announcement_id)
        
        # Only allow admin who created it to edit
        if announcement.user_id != session['admin_id']:
            return jsonify({'success': False, 'message': 'Permission denied'}), 403

        data = request.get_json(silent=True) or {}
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()

        if not title or not content:
            return jsonify({'success': False, 'message': 'Title and content are required'}), 400

        announcement.title = title
        announcement.content = content
        announcement.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'success': True, 'message': 'Announcement updated successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/delete-announcement/<int:announcement_id>', methods=['POST'])
def delete_announcement(announcement_id):
    """Delete announcement (admin only)"""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        announcement = Announcement.query.get_or_404(announcement_id)
        
        # Only allow admin who created it to delete
        if announcement.user_id != session['admin_id']:
            return jsonify({'success': False, 'message': 'Permission denied'}), 403

        # Delete associated comments first
        AnnouncementComment.query.filter_by(announcement_id=announcement_id).delete()
        AnnouncementView.query.filter_by(announcement_id=announcement_id).delete()
        
        db.session.delete(announcement)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Announcement deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/get-minutes')
def get_minutes():
    """Get minutes for current user"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    minutes = Minute.query.filter_by(user_id=session['user_id']).order_by(Minute.created_at.desc()).all()

    return jsonify({
        'success': True,
        'minutes': [{
            'id': m.id,
            'title': m.title,
            'meeting_date': m.meeting_date.isoformat() if m.meeting_date else None,
            'file_path': m.file_path,
            'created_at': m.created_at.isoformat()
        } for m in minutes]
    })


@app.route('/upload-minute', methods=['POST'])
def upload_minutes():
    """Upload meeting minutes"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        title = request.form.get('title')
        meeting_date = request.form.get('meeting_date')

        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        # Get the file extension from the original filename BEFORE secure_filename
        file_ext = ''
        if '.' in file.filename:
            file_ext = '.' + file.filename.rsplit('.', 1)[1].lower()
        
        # Generate safe filename with proper extension (add extension after secure_filename)
        safe_base = secure_filename(f"minutes_{session['user_id']}_{secrets.token_hex(8)}")
        filename = safe_base + file_ext
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Parse meeting date safely
        parsed_date = None
        if meeting_date:
            try:
                parsed_date = datetime.fromisoformat(meeting_date).date()
            except (ValueError, TypeError):
                pass

        minute = Minute(
            user_id=session['user_id'],
            title=title,
            meeting_date=parsed_date,
            file_path=filename
        )
        db.session.add(minute)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Minutes uploaded'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/delete-minute/<int:minute_id>', methods=['DELETE'])
def delete_minute(minute_id):
    """Delete minute"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        minute = Minute.query.filter_by(id=minute_id, user_id=session['user_id']).first()
        if not minute:
            return jsonify({'success': False, 'message': 'Minute not found'}), 404

        if minute.file_path:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], minute.file_path)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

        db.session.delete(minute)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Minute deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/update-minute', methods=['POST'])
def update_minute():
    """Update minute information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        minute_id = request.form.get('id')
        title = request.form.get('title')
        meeting_date = request.form.get('meeting_date')

        minute = Minute.query.filter_by(id=minute_id, user_id=session['user_id']).first()
        if not minute:
            return jsonify({'success': False, 'message': 'Minute not found'}), 404

        # Update title if provided
        if title:
            minute.title = title

        # Update meeting date if provided
        if meeting_date:
            try:
                minute.meeting_date = datetime.fromisoformat(meeting_date).date()
            except (ValueError, TypeError):
                pass

        # Handle file upload if provided
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                # Delete old file if exists
                if minute.file_path:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], minute.file_path)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass

                # Get the file extension from the original filename BEFORE secure_filename
                file_ext = ''
                if '.' in file.filename:
                    file_ext = '.' + file.filename.rsplit('.', 1)[1].lower()
                
                # Save new file with proper extension (add extension after secure_filename)
                safe_base = secure_filename(f"minutes_{session['user_id']}_{secrets.token_hex(8)}")
                filename = safe_base + file_ext
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                minute.file_path = filename

        minute.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'success': True, 'message': 'Minute updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== Resolutions Routes ====================

@app.route('/get-resolutions')
def get_resolutions():
    """Get resolutions for current user"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    resolutions = Resolution.query.filter_by(user_id=session['user_id']).order_by(Resolution.created_at.desc()).all()

    return jsonify({
        'success': True,
        'resolutions': [{
            'id': r.id,
            'resolution_number': r.resolution_number,
            'title': r.title,
            'date_passed': r.date_passed.isoformat() if r.date_passed else None,
            'file_path': r.file_path,
            'created_at': r.created_at.isoformat()
        } for r in resolutions]
    })


@app.route('/upload-resolution', methods=['POST'])
def upload_resolution():
    """Upload resolution"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        resolution_number = request.form.get('resolution_number')
        title = request.form.get('title')
        date_passed = request.form.get('date_passed')

        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        # Get the file extension from the original filename BEFORE secure_filename
        file_ext = ''
        if '.' in file.filename:
            file_ext = '.' + file.filename.rsplit('.', 1)[1].lower()
        
        # Generate safe filename with proper extension (add extension after secure_filename)
        safe_base = secure_filename(f"resolution_{session['user_id']}_{secrets.token_hex(8)}")
        filename = safe_base + file_ext
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Parse date safely
        parsed_date = None
        if date_passed:
            try:
                parsed_date = datetime.fromisoformat(date_passed).date()
            except (ValueError, TypeError):
                pass

        resolution = Resolution(
            user_id=session['user_id'],
            resolution_number=resolution_number,
            title=title,
            date_passed=parsed_date,
            file_path=filename
        )
        db.session.add(resolution)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Resolution uploaded'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/delete-resolution/<int:resolution_id>', methods=['DELETE'])
def delete_resolution(resolution_id):
    """Delete resolution file"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        resolution = Resolution.query.filter_by(id=resolution_id, user_id=session['user_id']).first()
        if not resolution:
            return jsonify({'success': False, 'message': 'Resolution not found'}), 404

        if resolution.file_path:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], resolution.file_path)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

        db.session.delete(resolution)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Resolution deleted'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/update-resolution', methods=['POST'])
def update_resolution_endpoint():
    """Update resolution information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        resolution_id = request.form.get('id')
        resolution_number = request.form.get('resolution_number')
        title = request.form.get('title')
        date_passed = request.form.get('date_passed')

        resolution = Resolution.query.filter_by(id=resolution_id, user_id=session['user_id']).first()
        if not resolution:
            return jsonify({'success': False, 'message': 'Resolution not found'}), 404

        # Update fields if provided
        if resolution_number:
            resolution.resolution_number = resolution_number
        if title:
            resolution.title = title
        if date_passed:
            try:
                resolution.date_passed = datetime.fromisoformat(date_passed).date()
            except (ValueError, TypeError):
                pass

        # Handle file upload if provided
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                # Delete old file if exists
                if resolution.file_path:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], resolution.file_path)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass

                # Get the file extension from the original filename BEFORE secure_filename
                file_ext = ''
                if '.' in file.filename:
                    file_ext = '.' + file.filename.rsplit('.', 1)[1].lower()
                
                # Save new file with proper extension (add extension after secure_filename)
                safe_base = secure_filename(f"resolution_{session['user_id']}_{secrets.token_hex(8)}")
                filename = safe_base + file_ext
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                resolution.file_path = filename

        resolution.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'success': True, 'message': 'Resolution updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== Budget for F.Y Routes ====================

@app.route('/create-budget-fy-template', methods=['POST'])
def create_budget_fy_template():
    """Create a new Budget for F.Y template"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        data = request.get_json(silent=True) or {}
        title = (data.get('title') or '').strip()
        fiscal_year = (data.get('fiscal_year') or '').strip()

        if not title:
            return jsonify({'success': False, 'message': 'Title is required'}), 400

        template = BudgetFYTemplate(
            user_id=session['user_id'],
            title=title,
            fiscal_year=fiscal_year or None
        )
        db.session.add(template)
        db.session.commit()

        return jsonify({'success': True, 'template_id': template.id})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/get-budget-fy-templates')
def get_budget_fy_templates():
    """List Budget for F.Y templates for current user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    templates = BudgetFYTemplate.query.filter_by(user_id=session['user_id']).order_by(BudgetFYTemplate.created_at.desc()).all()

    return jsonify({
        'success': True,
        'templates': [{
            'id': t.id,
            'title': t.title,
            'fiscal_year': t.fiscal_year,
            'created_at': t.created_at.isoformat(),
            'updated_at': t.updated_at.isoformat() if t.updated_at else None
        } for t in templates]
    })


@app.route('/get-budget-analytics')
def get_budget_analytics():
    """Get budget analytics data for dashboard"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        # Prefer budget project totals (reflects voucher disbursements)
        projects = BudgetProject.query.filter_by(user_id=session['user_id'], is_active=True).all()

        if projects:
            total_budget = sum(float(p.total_budget or 0) for p in projects)
            used_budget = sum(float(p.disbursed_amount or 0) for p in projects)
        else:
            # Fallback to Budget F.Y. templates if no projects exist
            templates = BudgetFYTemplate.query.filter_by(user_id=session['user_id']).all()

            total_budget = 0
            used_budget = 0
            fallback_total_budget = 0

            # Calculate totals from all templates
            for template in templates:
                rows = BudgetFYRow.query.filter_by(template_id=template.id).all()
                for row in rows:
                    amount = float(row.amount) if row.amount else 0
                    if row.row_type == 'TOTAL':
                        # Sum the amounts in total rows
                        total_budget += amount
                    else:
                        # Sum data rows as used budget
                        used_budget += amount
                        fallback_total_budget += amount

            # If no TOTAL rows exist, use the sum of DATA rows as total budget
            if total_budget == 0 and fallback_total_budget > 0:
                total_budget = fallback_total_budget
        
        return jsonify({
            'success': True,
            'total_budget': int(total_budget),
            'used_budget': int(used_budget)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/get-budget-fy-template/<int:template_id>')
def get_budget_fy_template(template_id):
    """Get Budget for F.Y template with rows"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    template = BudgetFYTemplate.query.filter_by(id=template_id, user_id=session['user_id']).first()
    if not template:
        return jsonify({'success': False, 'message': 'Template not found'}), 404

    rows = BudgetFYRow.query.filter_by(template_id=template.id).order_by(BudgetFYRow.sort_order.asc()).all()

    return jsonify({
        'success': True,
        'template': {
            'id': template.id,
            'title': template.title,
            'fiscal_year': template.fiscal_year,
            'rows': [{
                'id': row.id,
                'section': row.section,
                'program': row.program,
                'project_activities': row.project_activities,
                'account_code': row.account_code,
                'duration': row.duration,
                'mooe': row.mooe,
                'co': row.co,
                'amount': row.amount,
                'sort_order': row.sort_order
            } for row in rows]
        }
    })


@app.route('/save-budget-fy-template', methods=['POST'])
def save_budget_fy_template():
    """Save Budget for F.Y rows and template metadata"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        data = request.get_json(silent=True) or {}
        template_id = data.get('template_id')
        title = (data.get('title') or '').strip()
        fiscal_year = (data.get('fiscal_year') or '').strip()
        rows = data.get('rows', [])

        template = BudgetFYTemplate.query.filter_by(id=template_id, user_id=session['user_id']).first()
        if not template:
            return jsonify({'success': False, 'message': 'Template not found'}), 404

        if title:
            template.title = title
        template.fiscal_year = fiscal_year or None

        existing_rows = {row.id: row for row in BudgetFYRow.query.filter_by(template_id=template.id).all()}
        kept_ids = set()

        for idx, row_data in enumerate(rows):
            row_id = row_data.get('id')
            payload = {
                'section': row_data.get('section') or '',
                'program': row_data.get('program') or '',
                'project_activities': row_data.get('project_activities') or '',
                'account_code': row_data.get('account_code') or '',
                'duration': row_data.get('duration') or '',
                'mooe': float(row_data.get('mooe') or 0),
                'co': float(row_data.get('co') or 0),
                'amount': float(row_data.get('amount') or 0),
                'row_type': (row_data.get('row_type') or 'DATA').upper(),
                'sort_order': row_data.get('sort_order', idx)
            }

            if row_id and row_id in existing_rows:
                row = existing_rows[row_id]
                for key, value in payload.items():
                    setattr(row, key, value)
                kept_ids.add(row_id)
            else:
                row = BudgetFYRow(template_id=template.id, **payload)
                db.session.add(row)

        # Remove rows not kept
        for row_id, row in existing_rows.items():
            if row_id not in kept_ids:
                db.session.delete(row)

        db.session.commit()

        # Sync budget projects after saving template
        _sync_budget_projects_for_user(session['user_id'])

        return jsonify({'success': True, 'message': 'Budget for F.Y saved'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/delete-budget-fy-template/<int:template_id>', methods=['DELETE'])
def delete_budget_fy_template(template_id):
    """Delete a Budget for F.Y template and its rows"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        template = BudgetFYTemplate.query.filter_by(id=template_id, user_id=session['user_id']).first()
        if not template:
            return jsonify({'success': False, 'message': 'Template not found'}), 404

        # Delete all rows for this template
        BudgetFYRow.query.filter_by(template_id=template.id).delete()
        db.session.delete(template)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Template deleted'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


 # ==================== Budget Projects Routes ====================

def _sync_budget_projects_for_user(user_id):
    """Sync budget projects from Budget F.Y. templates for a user"""
    templates = BudgetFYTemplate.query.filter_by(user_id=user_id).all()
    synced_count = 0
    for template in templates:
        rows = BudgetFYRow.query.filter_by(template_id=template.id).all()

        for row in rows:
            # Only sync project rows (skip labels/totals)
            if (row.row_type or 'DATA').upper() != 'DATA':
                continue
            project_name = (row.project_activities or '').strip() or (row.program or '').strip()
            if not project_name:
                continue

            existing_project = BudgetProject.query.filter_by(
                user_id=user_id,
                budget_row_id=row.id
            ).first()

            if not existing_project:
                project = BudgetProject(
                    user_id=user_id,
                    template_id=template.id,
                    budget_row_id=row.id,
                    project_name=project_name,
                    fiscal_year=template.fiscal_year,
                    total_budget=row.amount or 0,
                    disbursed_amount=0,
                    remaining_balance=row.amount or 0,
                    account_code=row.account_code,
                    section=row.section,
                    program=row.program,
                    is_active=True
                )
                db.session.add(project)
                synced_count += 1
            else:
                existing_project.project_name = project_name
                existing_project.fiscal_year = template.fiscal_year
                existing_project.total_budget = row.amount or 0
                existing_project.remaining_balance = existing_project.total_budget - existing_project.disbursed_amount
                existing_project.account_code = row.account_code
                existing_project.section = row.section
                existing_project.program = row.program
                existing_project.updated_at = datetime.utcnow()

    db.session.commit()
    return synced_count

@app.route('/api/sync-budget-projects', methods=['POST'])
def sync_budget_projects():
    """Sync budget projects from Budget F.Y. templates"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        synced_count = _sync_budget_projects_for_user(session['user_id'])

        return jsonify({
            'success': True,
            'message': f'{synced_count} new projects synced',
            'synced_count': synced_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/budget-projects')
def get_budget_projects():
    """Get all budget projects for current user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        user_id = session['user_id']
        fiscal_year = request.args.get('fiscal_year')

        query = BudgetProject.query.filter_by(user_id=user_id, is_active=True)

        if fiscal_year:
            query = query.filter_by(fiscal_year=fiscal_year)

        projects = query.order_by(BudgetProject.created_at.desc()).all()

        return jsonify({
            'success': True,
            'projects': [{
                'id': p.id,
                'project_name': p.project_name,
                'fiscal_year': p.fiscal_year,
                'total_budget': p.total_budget,
                'disbursed_amount': p.disbursed_amount,
                'remaining_balance': p.remaining_balance,
                'account_code': p.account_code,
                'section': p.section,
                'program': p.program,
                'created_at': p.created_at.isoformat()
            } for p in projects]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/budget-projects/fiscal-years')
def get_budget_fiscal_years():
    """Get list of all fiscal years with budget projects"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        user_id = session['user_id']

        # Get distinct fiscal years from budget templates
        templates = BudgetFYTemplate.query.filter_by(user_id=user_id).all()
        fiscal_years = list(set([t.fiscal_year for t in templates if t.fiscal_year]))
        fiscal_years.sort(reverse=True)

        return jsonify({
            'success': True,
            'fiscal_years': fiscal_years
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== Liquidation Routes ====================

def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except Exception:
        return None


@app.route('/get-liquidation-reports')
def get_liquidation_reports():
    """List liquidation reports for current user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    reports = LiquidationReport.query.filter_by(user_id=session['user_id']).order_by(LiquidationReport.created_at.desc()).all()
    results = []
    for report in reports:
        items = LiquidationItem.query.filter_by(report_id=report.id).all()
        total_amount = sum(item.amount or 0 for item in items)
        results.append({
            'id': report.id,
            'lr_no': report.lr_no,
            'report_date': report.report_date.isoformat() if report.report_date else None,
            'barangay': report.barangay,
            'municipality': report.municipality,
            'province': report.province,
            'total_amount': total_amount,
            'created_at': report.created_at.isoformat() if report.created_at else None
        })

    return jsonify({'success': True, 'reports': results})


@app.route('/get-liquidation-report/<int:report_id>')
def get_liquidation_report(report_id):
    """Get liquidation report details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    report = LiquidationReport.query.filter_by(id=report_id, user_id=session['user_id']).first()
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404

    items = LiquidationItem.query.filter_by(report_id=report.id).order_by(LiquidationItem.sort_order.asc()).all()
    return jsonify({
        'success': True,
        'report': {
            'id': report.id,
            'lr_no': report.lr_no,
            'report_date': report.report_date.isoformat() if report.report_date else None,
            'barangay': report.barangay,
            'municipality': report.municipality,
            'province': report.province,
            'cash_advance_amount': report.cash_advance_amount,
            'cash_advance_dv_no': report.cash_advance_dv_no,
            'cash_advance_date': report.cash_advance_date.isoformat() if report.cash_advance_date else None,
            'refunded_amount': report.refunded_amount,
            'refunded_or_no': report.refunded_or_no,
            'refunded_date': report.refunded_date.isoformat() if report.refunded_date else None,
            'amount_reimbursed': report.amount_reimbursed,
            'certified_a_name': report.certified_a_name,
            'certified_b_name': report.certified_b_name,
            'certified_c_name': report.certified_c_name,
            'items': [{
                'id': item.id,
                'particulars': item.particulars,
                'amount': item.amount,
                'sort_order': item.sort_order
            } for item in items]
        }
    })


@app.route('/save-liquidation-report', methods=['POST'])
def save_liquidation_report():
    """Create or update liquidation report"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        data = request.get_json(silent=True) or {}
        report_id = data.get('id')
        items = data.get('items') or []

        if report_id:
            report = LiquidationReport.query.filter_by(id=report_id, user_id=session['user_id']).first()
            if not report:
                return jsonify({'success': False, 'message': 'Report not found'}), 404
        else:
            report = LiquidationReport(user_id=session['user_id'])
            db.session.add(report)

        report.lr_no = data.get('lr_no')
        report.report_date = _parse_date(data.get('report_date'))
        report.barangay = data.get('barangay')
        report.municipality = data.get('municipality')
        report.province = data.get('province')
        report.cash_advance_amount = float(data.get('cash_advance_amount') or 0)
        report.cash_advance_dv_no = data.get('cash_advance_dv_no')
        report.cash_advance_date = _parse_date(data.get('cash_advance_date'))
        report.refunded_amount = float(data.get('refunded_amount') or 0)
        report.refunded_or_no = data.get('refunded_or_no')
        report.refunded_date = _parse_date(data.get('refunded_date'))
        report.amount_reimbursed = float(data.get('amount_reimbursed') or 0)
        report.certified_a_name = data.get('certified_a_name')
        report.certified_b_name = data.get('certified_b_name')
        report.certified_c_name = data.get('certified_c_name')

        db.session.flush()

        LiquidationItem.query.filter_by(report_id=report.id).delete()
        for index, item in enumerate(items):
            row = LiquidationItem(
                report_id=report.id,
                particulars=item.get('particulars'),
                amount=float(item.get('amount') or 0),
                sort_order=index
            )
            db.session.add(row)

        db.session.commit()
        return jsonify({'success': True, 'report_id': report.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/delete-liquidation-report/<int:report_id>', methods=['DELETE'])
def delete_liquidation_report(report_id):
    """Delete liquidation report"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    report = LiquidationReport.query.filter_by(id=report_id, user_id=session['user_id']).first()
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404

    try:
        LiquidationItem.query.filter_by(report_id=report.id).delete()
        db.session.delete(report)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Report deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/print-liquidation-report/<int:report_id>')
def print_liquidation_report(report_id):
    """Printable liquidation report"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    report = LiquidationReport.query.filter_by(id=report_id, user_id=session['user_id']).first()
    if not report:
        return redirect(url_for('user_dashboard'))

    items = LiquidationItem.query.filter_by(report_id=report.id).order_by(LiquidationItem.sort_order.asc()).all()
    total_amount = sum(item.amount or 0 for item in items)
    return render_template('liquidation-print.html', report=report, items=items, total_amount=total_amount)


# ==================== APP (Annual Procurement Plan) Routes ====================

@app.route('/get-app-plans')
def get_app_plans():
    """Get all APP plans for user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    plans = AnnualProcurementPlan.query.filter_by(user_id=session['user_id']).order_by(AnnualProcurementPlan.created_at.desc()).all()
    return jsonify({
        'success': True,
        'plans': [{
            'id': p.id,
            'app_no': p.app_no,
            'barangay': p.barangay,
            'municipality': p.municipality,
            'calendar_year': p.calendar_year,
            'created_at': p.created_at.strftime('%Y-%m-%d')
        } for p in plans]
    })


@app.route('/get-app-plan/<int:plan_id>')
def get_app_plan(plan_id):
    """Get single APP plan with items"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    plan = AnnualProcurementPlan.query.filter_by(id=plan_id, user_id=session['user_id']).first()
    if not plan:
        return jsonify({'success': False, 'message': 'Plan not found'}), 404

    items = AppProcurementItem.query.filter_by(app_id=plan.id).order_by(AppProcurementItem.sort_order.asc()).all()
    return jsonify({
        'success': True,
        'plan': {
            'id': plan.id,
            'app_no': plan.app_no,
            'barangay': plan.barangay,
            'municipality': plan.municipality,
            'province': plan.province,
            'calendar_year': plan.calendar_year,
            'office_name': plan.office_name,
            'items': [{
                'id': i.id,
                'description': i.description,
                'unit_cost': i.unit_cost,
                'quantity': i.quantity,
                'unit': i.unit,
                'total_cost': i.total_cost,
                'q1_qty': i.q1_qty,
                'q1_amt': i.q1_amt,
                'q2_qty': i.q2_qty,
                'q2_amt': i.q2_amt,
                'q3_qty': i.q3_qty,
                'q3_amt': i.q3_amt,
                'q4_qty': i.q4_qty,
                'q4_amt': i.q4_amt,
            } for i in items]
        }
    })


@app.route('/save-app-plan', methods=['POST'])
def save_app_plan():
    """Create/update APP plan"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        data = request.get_json(silent=True) or {}
        plan_id = data.get('plan_id')
        app_no = data.get('app_no', '')
        barangay = data.get('barangay', '')
        municipality = data.get('municipality', '')
        province = data.get('province', '')
        calendar_year = int(data.get('calendar_year', 0)) if data.get('calendar_year') else None
        office_name = data.get('office_name', '')
        items_data = data.get('items', [])

        if plan_id:
            plan = AnnualProcurementPlan.query.filter_by(id=plan_id, user_id=session['user_id']).first()
            if not plan:
                return jsonify({'success': False, 'message': 'Plan not found'}), 404
        else:
            plan = AnnualProcurementPlan(user_id=session['user_id'])

        plan.app_no = app_no
        plan.barangay = barangay
        plan.municipality = municipality
        plan.province = province
        plan.calendar_year = calendar_year
        plan.office_name = office_name

        db.session.add(plan)
        db.session.flush()

        AppProcurementItem.query.filter_by(app_id=plan.id).delete()

        for idx, item_data in enumerate(items_data):
            item = AppProcurementItem(
                app_id=plan.id,
                description=item_data.get('description', ''),
                unit_cost=float(item_data.get('unit_cost', 0)) if item_data.get('unit_cost') else 0,
                quantity=float(item_data.get('quantity', 0)) if item_data.get('quantity') else 0,
                unit=item_data.get('unit', ''),
                total_cost=float(item_data.get('total_cost', 0)) if item_data.get('total_cost') else 0,
                q1_qty=float(item_data.get('q1_qty', 0)) if item_data.get('q1_qty') else 0,
                q1_amt=float(item_data.get('q1_amt', 0)) if item_data.get('q1_amt') else 0,
                q2_qty=float(item_data.get('q2_qty', 0)) if item_data.get('q2_qty') else 0,
                q2_amt=float(item_data.get('q2_amt', 0)) if item_data.get('q2_amt') else 0,
                q3_qty=float(item_data.get('q3_qty', 0)) if item_data.get('q3_qty') else 0,
                q3_amt=float(item_data.get('q3_amt', 0)) if item_data.get('q3_amt') else 0,
                q4_qty=float(item_data.get('q4_qty', 0)) if item_data.get('q4_qty') else 0,
                q4_amt=float(item_data.get('q4_amt', 0)) if item_data.get('q4_amt') else 0,
                row_type=item_data.get('row_type', 'DATA'),
                sort_order=idx
            )
            db.session.add(item)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Plan saved', 'plan_id': plan.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/delete-app-plan/<int:plan_id>', methods=['DELETE'])
def delete_app_plan(plan_id):
    """Delete APP plan"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        plan = AnnualProcurementPlan.query.filter_by(id=plan_id, user_id=session['user_id']).first()
        if not plan:
            return jsonify({'success': False, 'message': 'Plan not found'}), 404

        AppProcurementItem.query.filter_by(app_id=plan.id).delete()
        db.session.delete(plan)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Plan deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/print-app-plan/<int:plan_id>')
def print_app_plan(plan_id):
    """Printable APP plan"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    plan = AnnualProcurementPlan.query.filter_by(id=plan_id, user_id=session['user_id']).first()
    if not plan:
        return redirect(url_for('user_dashboard'))

    items = AppProcurementItem.query.filter_by(app_id=plan.id).order_by(AppProcurementItem.sort_order.asc()).all()
    return render_template('app-print.html', plan=plan, items=items)


# ==================== Password Change Routes ====================

@app.route('/request-password-change', methods=['POST'])
def request_password_change():
    """User requests password change"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        data = request.get_json(silent=True) or {}
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        if not check_password_hash(user.password_hash, current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400

        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'}), 400

        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400

        # Check for existing pending request
        existing = PasswordChangeRequest.query.filter_by(user_id=session['user_id'], status='pending').first()
        if existing:
            return jsonify({'success': False, 'message': 'You already have a pending password change request'}), 400

        request_record = PasswordChangeRequest(
            user_id=session['user_id'],
            new_password_hash=generate_password_hash(new_password),
            status='pending'
        )
        db.session.add(request_record)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Password change request submitted for admin approval'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/get-password-change-status')
def get_password_change_status():
    """Get password change request status"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    request_record = PasswordChangeRequest.query.filter_by(user_id=session['user_id']).order_by(PasswordChangeRequest.created_at.desc()).first()

    if request_record:
        return jsonify({
            'success': True,
            'request': {
                'id': request_record.id,
                'status': request_record.status,
                'notes': request_record.notes,
                'created_at': request_record.created_at.isoformat()
            }
        })

    return jsonify({'success': True, 'request': None})


@app.route('/get-password-change-requests')
def get_password_change_requests():
    """Admin gets all pending password change requests"""
    if 'admin_id' not in session:
        return jsonify({'success': False}), 401

    requests = PasswordChangeRequest.query.filter_by(status='pending').all()

    return jsonify({
        'success': True,
        'requests': [{
            'id': r.id,
            'user_id': r.user_id,
            'user_email': User.query.get(r.user_id).email if User.query.get(r.user_id) else 'Unknown',
            'created_at': r.created_at.isoformat()
        } for r in requests]
    })


@app.route('/approve-password-change/<int:request_id>', methods=['POST'])
def approve_password_change(request_id):
    """Admin approves password change"""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        request_record = PasswordChangeRequest.query.get(request_id)
        if not request_record:
            return jsonify({'success': False, 'message': 'Request not found'}), 404

        user = User.query.get(request_record.user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Update user password
        user.password_hash = request_record.new_password_hash
        user.last_password_change = datetime.utcnow()
        user.current_password = None

        # Record password history
        history = PasswordHistory(
            user_id=request_record.user_id,
            password_plain=None,
            changed_by='admin'
        )
        db.session.add(history)

        # Mark request as approved
        request_record.status = 'approved'
        request_record.approved_by = session['admin_id']
        request_record.approval_date = datetime.utcnow()

        db.session.commit()

        return jsonify({'success': True, 'message': 'Password change approved'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/reject-password-change/<int:request_id>', methods=['POST'])
def reject_password_change(request_id):
    """Admin rejects password change"""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        data = request.get_json(silent=True) or {}
        notes = data.get('notes', '')

        request_record = PasswordChangeRequest.query.get(request_id)
        if not request_record:
            return jsonify({'success': False, 'message': 'Request not found'}), 404

        request_record.status = 'rejected'
        request_record.notes = notes

        db.session.commit()

        return jsonify({'success': True, 'message': 'Password change rejected'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/get-user-passwords/<int:user_id>')
def get_user_passwords(user_id):
    """Admin can view all password changes for a user"""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user = User.query.get_or_404(user_id)
    password_history = PasswordHistory.query.filter_by(user_id=user_id).order_by(PasswordHistory.changed_at.desc()).all()
    
    return jsonify({
        'success': True,
        'user_email': user.email,
        'current_password': user.current_password,
        'history': [{
            'password': ph.password_plain,
            'changed_at': ph.changed_at.isoformat(),
            'changed_by': ph.changed_by
        } for ph in password_history]
    })


@app.route('/get-user-full-details/<int:user_id>')
def get_user_full_details(user_id):
    """Admin fetches full user details and profile"""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    user = User.query.get_or_404(user_id)
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    approval = AccountApproval.query.filter_by(user_id=user_id).order_by(AccountApproval.created_at.desc()).first()

    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'approval_status': approval.status if approval else 'pending',
            'profile': {
                'full_name': profile.full_name if profile else None,
                'position': profile.position if profile else None,
                'barangay': profile.barangay if profile else None,
                'municipality': profile.municipality if profile else None,
                'birthdate': profile.birthdate.isoformat() if profile and profile.birthdate else None,
                'profile_picture': normalize_upload_filename(profile.profile_picture) if profile else None,
                'brgy_sk_logo': normalize_upload_filename(profile.brgy_sk_logo) if profile else None,
                'is_completed': profile.is_completed if profile else False
            }
        }
    })


# ==================== Admin Routes ====================

@app.route('/get-unread-notifications-count')
def get_unread_notifications_count():
    """Get count of unread announcements"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    viewed_ids = db.session.query(AnnouncementView.announcement_id).filter_by(user_id=session['user_id']).all()
    viewed_ids = set(id[0] for id in viewed_ids)

    announcements = Announcement.query.all()
    unread_count = sum(1 for a in announcements if a.id not in viewed_ids)

    return jsonify({'success': True, 'count': unread_count})


@app.route('/user-announcements')
def user_announcements():
    """User announcements page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('user-announcements.html')


@app.route('/disbursement-voucher')
def disbursement_voucher():
    """Disbursement voucher page - accessible by users"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('disbursement-voucher.html')


@app.route('/voucher-history')
def voucher_history():
    """Voucher history and records page - accessible by users"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('voucher-history.html')


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files with proper headers for inline viewing."""
    import os
    import re
    
    normalized_filename = normalize_upload_filename(filename)
    if not normalized_filename:
        print(f"Invalid filename format: {filename}")
        return jsonify({'success': False, 'message': 'Invalid filename format'}), 400
    filename = normalized_filename
    
    # Validate filename - allow alphanumeric, underscore, hyphen, dot only
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
        print(f"Invalid filename format: {filename}")
        return jsonify({'success': False, 'message': 'Invalid filename format'}), 400
    
    # Prevent directory traversal
    if '..' in filename or '/' in filename:
        print(f"Path traversal attempt: {filename}")
        return jsonify({'success': False, 'message': 'Invalid path'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Double-check that file_path is within UPLOAD_FOLDER
    real_path = os.path.realpath(file_path)
    real_upload_folder = os.path.realpath(app.config['UPLOAD_FOLDER'])
    if not real_path.startswith(real_upload_folder):
        print(f"Path traversal blocked: {real_path}")
        return jsonify({'success': False, 'message': 'Invalid path'}), 400
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return jsonify({'success': False, 'message': f'File not found: {filename}'}), 404
    
    # Determine MIME type based on file extension
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    mime_types = {
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'jfif': 'image/jpeg',
        'jpe': 'image/jpeg',
        'bmp': 'image/bmp',
        'svg': 'image/svg+xml'
    }
    mime_type = mime_types.get(file_ext, 'application/octet-stream')
    
    # Serve with inline disposition for viewable files
    if file_ext in ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp', 'txt', 'jfif', 'jpe', 'bmp', 'svg']:
        try:
            response = send_from_directory(app.config['UPLOAD_FOLDER'], filename)
            response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
            response.headers['Content-Type'] = mime_type
            response.headers['Cache-Control'] = 'public, max-age=3600'
            return response
        except Exception as e:
            print(f"Error serving file: {e}")
            return jsonify({'success': False, 'message': f'Error serving file: {str(e)}'}), 500
    else:
        # Force download for other file types
        try:
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
        except Exception as e:
            print(f"Error downloading file: {e}")
            return jsonify({'success': False, 'message': f'Error downloading file: {str(e)}'}), 500


def init_db():
    """Initialize database with tables"""
    with app.app_context():
        db.create_all()

        # Ensure announcement.view_count exists
        try:
            result = db.session.execute(text("PRAGMA table_info(announcement)"))
            columns = {row[1] for row in result.fetchall()}
            if 'view_count' not in columns:
                db.session.execute(text("ALTER TABLE announcement ADD COLUMN view_count INTEGER DEFAULT 0"))
                db.session.commit()
        except Exception as exc:
            print(f"Announcement migration warning: {exc}")

        # Ensure announcement_view table exists
        try:
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='announcement_view'"))
            if not result.fetchone():
                db.session.execute(text(
                    "CREATE TABLE announcement_view ("
                    "id INTEGER PRIMARY KEY, "
                    "announcement_id INTEGER NOT NULL, "
                    "user_id INTEGER NOT NULL, "
                    "viewed_at DATETIME, "
                    "FOREIGN KEY(announcement_id) REFERENCES announcement(id), "
                    "FOREIGN KEY(user_id) REFERENCES user(id)"
                    ")"
                ))
                db.session.commit()
        except Exception as exc:
            print(f"Announcement view migration warning: {exc}")

        # Ensure announcement_file table exists
        try:
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='announcement_file'"))
            if not result.fetchone():
                db.session.execute(text(
                    "CREATE TABLE announcement_file ("
                    "id INTEGER PRIMARY KEY, "
                    "announcement_id INTEGER NOT NULL, "
                    "user_id INTEGER NOT NULL, "
                    "filename VARCHAR(300) NOT NULL, "
                    "file_path VARCHAR(300) NOT NULL, "
                    "created_at DATETIME, "
                    "FOREIGN KEY(announcement_id) REFERENCES announcement(id), "
                    "FOREIGN KEY(user_id) REFERENCES user(id)"
                    ")"
                ))
                db.session.commit()
        except Exception as exc:
            print(f"Announcement file migration warning: {exc}")

        # Ensure budget_project table exists
        try:
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='budget_project'"))
            if not result.fetchone():
                db.session.execute(text(
                    "CREATE TABLE budget_project ("
                    "id INTEGER PRIMARY KEY, "
                    "user_id INTEGER NOT NULL, "
                    "template_id INTEGER NOT NULL, "
                    "budget_row_id INTEGER NOT NULL, "
                    "project_name TEXT NOT NULL, "
                    "fiscal_year VARCHAR(50), "
                    "total_budget FLOAT DEFAULT 0, "
                    "disbursed_amount FLOAT DEFAULT 0, "
                    "remaining_balance FLOAT DEFAULT 0, "
                    "account_code VARCHAR(50), "
                    "section VARCHAR(200), "
                    "program VARCHAR(200), "
                    "is_active BOOLEAN DEFAULT 1, "
                    "created_at DATETIME, "
                    "updated_at DATETIME, "
                    "FOREIGN KEY(user_id) REFERENCES user(id), "
                    "FOREIGN KEY(template_id) REFERENCES budget_fy_template(id), "
                    "FOREIGN KEY(budget_row_id) REFERENCES budget_fy_row(id)"
                    ")"
                ))
                db.session.commit()
        except Exception as exc:
            print(f"Budget project migration warning: {exc}")

        # Ensure budget_fy_row row_type column exists
        try:
            result = db.session.execute(text("PRAGMA table_info(budget_fy_row)"))
            columns = {row[1] for row in result.fetchall()}
            if 'row_type' not in columns:
                db.session.execute(text("ALTER TABLE budget_fy_row ADD COLUMN row_type VARCHAR(50) DEFAULT 'DATA'"))
                db.session.commit()
        except Exception as exc:
            print(f"Budget FY row migration warning: {exc}")

        # Ensure voucher_budget_allocation table exists
        try:
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='voucher_budget_allocation'"))
            if not result.fetchone():
                db.session.execute(text(
                    "CREATE TABLE voucher_budget_allocation ("
                    "id INTEGER PRIMARY KEY, "
                    "voucher_id INTEGER NOT NULL, "
                    "budget_project_id INTEGER NOT NULL, "
                    "allocated_amount FLOAT NOT NULL, "
                    "created_at DATETIME, "
                    "FOREIGN KEY(voucher_id) REFERENCES dis_voucher(id), "
                    "FOREIGN KEY(budget_project_id) REFERENCES budget_project(id)"
                    ")"
                ))
                db.session.commit()
        except Exception as exc:
            print(f"Voucher budget allocation migration warning: {exc}")

        # Ensure user_profile new columns exist
        try:
            result = db.session.execute(text("PRAGMA table_info(user_profile)"))
            columns = {row[1] for row in result.fetchall()}
            if 'phone_no' not in columns:
                db.session.execute(text("ALTER TABLE user_profile ADD COLUMN phone_no VARCHAR(20)"))
            if 'email' not in columns:
                db.session.execute(text("ALTER TABLE user_profile ADD COLUMN email VARCHAR(120)"))
            if 'complete_address' not in columns:
                db.session.execute(text("ALTER TABLE user_profile ADD COLUMN complete_address TEXT"))
            db.session.commit()
        except Exception as exc:
            print(f"User profile migration warning: {exc}")

        # Ensure user_creation_log table exists
        try:
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_creation_log'"))
            if not result.fetchone():
                db.session.execute(text(
                    "CREATE TABLE user_creation_log ("
                    "id INTEGER PRIMARY KEY, "
                    "user_id INTEGER NOT NULL, "
                    "created_by_admin_id INTEGER NOT NULL, "
                    "user_email VARCHAR(120) NOT NULL, "
                    "admin_email VARCHAR(120) NOT NULL, "
                    "created_at DATETIME, "
                    "FOREIGN KEY(user_id) REFERENCES user(id), "
                    "FOREIGN KEY(created_by_admin_id) REFERENCES admin(id)"
                    ")"
                ))
                db.session.commit()
        except Exception as exc:
            print(f"User creation log migration warning: {exc}")
        
        # Create super admin if not exists
        if not Admin.query.filter_by(email='admin@sklgu.gov.ph').first():
            super_admin = Admin(
                email='admin@sklgu.gov.ph',
                password_hash=generate_password_hash('admin123'),  # Change this!
                is_super_admin=True
            )
            db.session.add(super_admin)
            db.session.commit()
            print("Super admin created: admin@sklgu.gov.ph / admin123")
        
        # Create test user if not exists
        if not User.query.filter_by(email='user@sklgu.gov.ph').first():
            test_user = User(
                email='user@sklgu.gov.ph',
                password_hash=generate_password_hash('user123'),
                account_status='active'
            )
            db.session.add(test_user)
            db.session.commit()
            
            # Create user profile
            user_profile = UserProfile(
                user_id=test_user.id,
                full_name='Test User',
                position='Member',
                barangay='Barangay 1',
                municipality='Municipality',
                is_completed=True
            )
            db.session.add(user_profile)
            db.session.commit()
            print("Test user created: user@sklgu.gov.ph / user123")


# ==================== Missing API Routes ====================

@app.route('/check-auth')
def check_auth():
    """Check if user/admin is authenticated"""
    if 'admin_id' in session:
        return jsonify({'authenticated': True, 'type': 'admin', 'email': session.get('admin_email')})
    elif 'user_id' in session:
        return jsonify({'authenticated': True, 'type': 'user', 'email': session.get('user_email')})
    return jsonify({'authenticated': False}), 401


@app.route('/get-pending-accounts')
def get_pending_accounts():
    """Get pending user accounts for admin approval"""
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    pending_accounts = AccountApproval.query.filter_by(status='pending').all()
    result = []
    for approval in pending_accounts:
        user = User.query.get(approval.user_id)
        profile = UserProfile.query.filter_by(user_id=approval.user_id).first()
        result.append({
            'id': approval.id,
            'user_id': user.id,
            'email': user.email,
            'full_name': profile.full_name if profile else '',
            'barangay': profile.barangay if profile else '',
            'created_at': user.created_at.isoformat()
        })
    return jsonify({'success': True, 'pending_accounts': result})


@app.route('/get-users')
def get_users():
    """Get all users (admin or user session)"""
    if 'admin_id' not in session and 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    users = User.query.all()
    result = []
    for user in users:
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        result.append({
            'id': user.id,
            'email': user.email,
            'full_name': profile.full_name if profile else '',
            'barangay': profile.barangay if profile else '',
            'profile_picture': normalize_upload_filename(profile.profile_picture) if profile and profile.profile_picture else '',
            'created_at': user.created_at.isoformat()
        })
    return jsonify({'success': True, 'users': result})


@app.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user and all their associated records (Admin only)"""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Delete all associated records in order (respect foreign key constraints)
        
        # 1. Delete announcement-related records
        announcements = Announcement.query.filter_by(user_id=user_id).all()
        for announcement in announcements:
            # Delete announcement comments
            AnnouncementComment.query.filter_by(announcement_id=announcement.id).delete()
            # Delete announcement views
            AnnouncementView.query.filter_by(announcement_id=announcement.id).delete()
            # Delete announcement files
            AnnouncementFile.query.filter_by(announcement_id=announcement.id).delete()
            # Delete announcement likes
            AnnouncementLike.query.filter_by(announcement_id=announcement.id).delete()
            # Delete announcement notifications
            AnnouncementNotification.query.filter_by(announcement_id=announcement.id).delete()
        
        # Delete user's own announcement interactions
        AnnouncementComment.query.filter_by(user_id=user_id).delete()
        AnnouncementView.query.filter_by(user_id=user_id).delete()
        AnnouncementFile.query.filter_by(user_id=user_id).delete()
        AnnouncementLike.query.filter_by(user_id=user_id).delete()
        AnnouncementNotification.query.filter_by(user_id=user_id).delete()
        
        # Delete announcements
        Announcement.query.filter_by(user_id=user_id).delete()
        
        # 2. Delete disbursement vouchers and their line items
        vouchers = DisVoucher.query.filter_by(user_id=user_id).all()
        for voucher in vouchers:
            DisVoucherLine.query.filter_by(voucher_id=voucher.id).delete()
            VoucherBudgetAllocation.query.filter_by(voucher_id=voucher.id).delete()
        DisVoucher.query.filter_by(user_id=user_id).delete()
        
        # 3. Delete liquidation reports and items
        liquidation_reports = LiquidationReport.query.filter_by(user_id=user_id).all()
        for report in liquidation_reports:
            LiquidationItem.query.filter_by(report_id=report.id).delete()
        LiquidationReport.query.filter_by(user_id=user_id).delete()
        
        # 4. Delete APP plans and items
        app_plans = AnnualProcurementPlan.query.filter_by(user_id=user_id).all()
        for plan in app_plans:
            AppProcurementItem.query.filter_by(app_id=plan.id).delete()
        AnnualProcurementPlan.query.filter_by(user_id=user_id).delete()
        
        # 5. Delete budget templates and rows
        budget_templates = BudgetFYTemplate.query.filter_by(user_id=user_id).all()
        for template in budget_templates:
            BudgetFYRow.query.filter_by(template_id=template.id).delete()
        BudgetFYTemplate.query.filter_by(user_id=user_id).delete()
        
        # 6. Delete budget projects
        BudgetProject.query.filter_by(user_id=user_id).delete()
        
        # 7. Delete other user records
        DisbursementReport.query.filter_by(user_id=user_id).delete()
        Minute.query.filter_by(user_id=user_id).delete()
        Resolution.query.filter_by(user_id=user_id).delete()
        InventoryItem.query.filter_by(user_id=user_id).delete()
        
        # 8. Delete password-related records
        PasswordChangeRequest.query.filter_by(user_id=user_id).delete()
        PasswordHistory.query.filter_by(user_id=user_id).delete()
        
        # 9. Delete account approval records
        AccountApproval.query.filter_by(user_id=user_id).delete()
        
        # 10. Delete user creation log
        UserCreationLog.query.filter_by(user_id=user_id).delete()
        
        # 11. Delete user profile
        UserProfile.query.filter_by(user_id=user_id).delete()
        
        # 12. Finally, delete the user
        db.session.delete(user)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'User {user.email} and all associated records deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting user: {str(e)}'}), 500


@app.route('/get-analytics-data')
def get_analytics_data():
    """Get analytics data for dashboard"""
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get all users count
        total_users = User.query.count()
        
        # Get approved users count (use account_status)
        approved_users = User.query.filter(User.account_status.in_(['active', 'approved'])).count()

        # Active users map to approved/active accounts
        active_users = approved_users
        
        # Get users by municipality
        profiles = UserProfile.query.all()
        municipality_counts = {}
        position_counts = {}
        
        for profile in profiles:
            if profile.municipality:
                municipality = profile.municipality
                municipality_counts[municipality] = municipality_counts.get(municipality, 0) + 1
            if profile.position:
                position = profile.position
                position_counts[position] = position_counts.get(position, 0) + 1
        
        # Prepare municipality data
        if municipality_counts:
            sorted_munic = sorted(municipality_counts.items(), key=lambda x: x[1], reverse=True)
            municipality_data = {
                'labels': [m[0] for m in sorted_munic[:10]],
                'values': [m[1] for m in sorted_munic[:10]]
            }
        else:
            municipality_data = {'labels': ['No Data'], 'values': [0]}
        
        # Prepare position data
        if position_counts:
            sorted_pos = sorted(position_counts.items(), key=lambda x: x[1], reverse=True)
            position_data = {
                'labels': [p[0] for p in sorted_pos[:10]],
                'values': [p[1] for p in sorted_pos[:10]]
            }
        else:
            position_data = {'labels': ['No Data'], 'values': [0]}
        
        # Get approval status distribution based on account_status
        approved_count = User.query.filter(User.account_status.in_(['active', 'approved'])).count()
        pending_count = User.query.filter_by(account_status='pending').count()
        rejected_count = User.query.filter_by(account_status='rejected').count()
        
        approval_data = {
            'labels': ['Approved', 'Pending', 'Rejected'],
            'values': [approved_count, pending_count, rejected_count]
        }
        
        # Active vs inactive
        inactive_users = max(0, total_users - active_users)
        active_data = {
            'active': active_users,
            'inactive': inactive_users
        }
        
        return jsonify({
            'success': True,
            'total_users': total_users,
            'approved_users': approved_users,
            'active_users': active_users,
            'municipality_data': municipality_data,
            'position_data': position_data,
            'approval_data': approval_data,
            'active_data': active_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/get-announcements-details')
def get_announcements_details():
    """Get announcement details with comments (admin or user session)"""
    if 'admin_id' not in session and 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    result = []
    for ann in announcements:
        # Check if posted by admin or user
        admin = Admin.query.get(ann.user_id)
        user = User.query.get(ann.user_id) if not admin else None
        
        comments = AnnouncementComment.query.filter_by(announcement_id=ann.id).all()
        comment_list = []
        for comment in comments:
            comment_user = User.query.get(comment.user_id)
            comment_list.append({
                'id': comment.id,
                'comment': comment.comment,
                'user_email': comment_user.email if comment_user else 'Unknown',
                'posted_at': comment.created_at.isoformat()
            })
        
        # Get likes information
        likes = AnnouncementLike.query.filter_by(announcement_id=ann.id).all()
        like_list = []
        for like in likes:
            like_user = User.query.get(like.user_id)
            if like_user:
                like_profile = UserProfile.query.filter_by(user_id=like.user_id).first()
                like_list.append({
                    'user_id': like.user_id,
                    'user_email': like_user.email,
                    'user_name': like_profile.full_name if like_profile else like_user.email,
                    'liked_at': like.created_at.isoformat()
                })
        
        result.append({
            'id': ann.id,
            'title': ann.title,
            'content': ann.content,
            'author': f'Admin ({admin.email})' if admin else (user.email if user else 'Unknown'),
            'view_count': ann.view_count,
            'comment_count': len(comments),
            'like_count': len(likes),
            'likes': like_list,
            'comments': comment_list,
            'posted_at': ann.created_at.isoformat(),
            'created_at': ann.created_at.isoformat()
        })
    return jsonify({'success': True, 'announcements': result})


@app.route('/get-announcement-likes/<int:announcement_id>')
def get_announcement_likes(announcement_id):
    """Get all users who liked an announcement"""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    likes = AnnouncementLike.query.filter_by(announcement_id=announcement_id).all()
    like_list = []
    
    for like in likes:
        user = User.query.get(like.user_id)
        if user:
            profile = UserProfile.query.filter_by(user_id=like.user_id).first()
            like_list.append({
                'user_id': like.user_id,
                'email': user.email,
                'full_name': profile.full_name if profile else user.email,
                'liked_at': like.created_at.isoformat()
            })
    
    return jsonify({
        'success': True,
        'likes': like_list,
        'total': len(like_list)
    })


@app.route('/get-admin-notifications')
def get_admin_notifications():
    """Get unread notifications for admin about announcement interactions"""
    if 'admin_id' not in session:
        return jsonify({'success': False}), 401
    
    # Get all announcements posted by this admin
    admin_announcements = Announcement.query.filter_by(user_id=session['admin_id']).all()
    announcement_ids = [a.id for a in admin_announcements]
    
    # Get unread notifications
    notifications = AnnouncementNotification.query.filter(
        AnnouncementNotification.announcement_id.in_(announcement_ids),
        AnnouncementNotification.is_read == False
    ).order_by(AnnouncementNotification.created_at.desc()).all()
    
    notif_list = []
    for notif in notifications:
        user = User.query.get(notif.user_id)
        announcement = Announcement.query.get(notif.announcement_id)
        profile = UserProfile.query.filter_by(user_id=notif.user_id).first()
        
        notif_list.append({
            'id': notif.id,
            'announcement_id': notif.announcement_id,
            'announcement_title': announcement.title if announcement else 'Unknown',
            'user_name': profile.full_name if profile else (user.email if user else 'Unknown'),
            'user_email': user.email if user else 'Unknown',
            'type': notif.notification_type,
            'created_at': notif.created_at.isoformat()
        })
    
    return jsonify({
        'success': True,
        'notifications': notif_list,
        'count': len(notif_list)
    })


@app.route('/mark-notifications-read', methods=['POST'])
def mark_notifications_read():
    """Mark all notifications as read"""
    if 'admin_id' not in session:
        return jsonify({'success': False}), 401
    
    admin_announcements = Announcement.query.filter_by(user_id=session['admin_id']).all()
    announcement_ids = [a.id for a in admin_announcements]
    
    AnnouncementNotification.query.filter(
        AnnouncementNotification.announcement_id.in_(announcement_ids)
    ).update({'is_read': True})
    
    db.session.commit()
    return jsonify({'success': True})


def generate_dv_number(user_id, year=None):
    """Generate DV number in format: YYYY-(MONTH)-(SEQUENCE)
    Example: 2026-02-001"""
    from datetime import datetime
    if year is None:
        year = datetime.now().year
    month = datetime.now().month

    # Count existing vouchers for this month (global, not per-user)
    existing_count = DisVoucher.query.filter(
        DisVoucher.dv_number.like(f'{year}-{month:02d}-%')
    ).count()

    sequence = existing_count + 1
    dv_number = f'{year}-{month:02d}-{sequence:03d}'

    # Ensure uniqueness in case of collisions
    while DisVoucher.query.filter_by(dv_number=dv_number).first() is not None:
        sequence += 1
        dv_number = f'{year}-{month:02d}-{sequence:03d}'

    return dv_number


@app.route('/api/disbursement-voucher', methods=['POST'])
def create_disbursement_voucher():
    """Create a new disbursement voucher"""
    print(f"[DEBUG] POST /api/disbursement-voucher - Session: {dict(session)}")
    print(f"[DEBUG] Request headers: {dict(request.headers)}")
    
    if 'user_id' not in session:
        print(f"[DEBUG] No user_id in session. Available keys: {list(session.keys())}")
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    try:
        user_id = session['user_id']
        data = request.get_json(silent=True) or {}
        print(f"[DEBUG] Creating voucher for user_id: {user_id}, data: {data}")
        
        # Validate budget project selection
        budget_project_id = data.get('budget_project_id')
        disbursement_amount = float(data.get('amount_due', 0)) if data.get('amount_due') else 0
        
        if not budget_project_id:
            return jsonify({
                'success': False,
                'message': 'Please select a budget project before saving the voucher'
            }), 400
        
        if disbursement_amount <= 0:
            return jsonify({
                'success': False,
                'message': 'Please enter a valid disbursement amount'
            }), 400
        
        # Get the budget project
        budget_project = BudgetProject.query.filter_by(
            id=budget_project_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not budget_project:
            return jsonify({
                'success': False,
                'message': 'Budget project not found or inactive'
            }), 404
        
        # Check if there's enough remaining balance
        if disbursement_amount > budget_project.remaining_balance:
            return jsonify({
                'success': False,
                'message': f'OPS, SUMOBRA KA. Remaining balance: ₱{budget_project.remaining_balance:,.2f}'
            }), 400
        
        # Generate DV number
        dv_number = generate_dv_number(user_id)
        print(f"[DEBUG] Generated DV number: {dv_number}")
        
        # Create voucher
        voucher = DisVoucher(
            user_id=user_id,
            dv_number=dv_number,
            barangay=data.get('barangay', ''),
            payee=data.get('payee', ''),
            address=data.get('address', ''),
            tin=data.get('tin', ''),
            province=data.get('province', ''),
            responsibility_center=data.get('responsibility_center', ''),
            fund_cluster=data.get('fund_cluster', ''),
            particulars=data.get('particulars', ''),
                total_amount=disbursement_amount,
            check_number=data.get('check_number', ''),
            bank_name=data.get('bank_name', ''),
            or_number=data.get('or_number', ''),
            status='draft'
        )
        
        # Parse dates if provided
        if data.get('voucher_date'):
            try:
                voucher.voucher_date = datetime.fromisoformat(data['voucher_date']).date()
            except:
                pass
        
        if data.get('payment_date'):
            try:
                voucher.payment_date = datetime.fromisoformat(data['payment_date']).date()
            except:
                pass
        
        db.session.add(voucher)
        db.session.flush()  # Get voucher ID before committing
        
        # Create budget allocation record
        allocation = VoucherBudgetAllocation(
            voucher_id=voucher.id,
            budget_project_id=budget_project.id,
            allocated_amount=disbursement_amount
        )
        db.session.add(allocation)
        
        # Update budget project - deduct the disbursed amount
        budget_project.disbursed_amount += disbursement_amount
        budget_project.remaining_balance = budget_project.total_budget - budget_project.disbursed_amount
        budget_project.updated_at = datetime.utcnow()
        
        db.session.commit()
        print(f"[DEBUG] Voucher created successfully with ID: {voucher.id}")
        
        return jsonify({
            'success': True,
            'message': f'Voucher created successfully. ₱{disbursement_amount:,.2f} deducted from budget project.',
            'dv_number': dv_number,
            'voucher_id': voucher.id,
            'remaining_budget': budget_project.remaining_balance
        })
    except Exception as e:
        print(f"[DEBUG] Exception creating voucher: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/disbursement-voucher/<int:voucher_id>', methods=['PUT'])
def update_disbursement_voucher(voucher_id):
    """Update an existing disbursement voucher"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        voucher = DisVoucher.query.get_or_404(voucher_id)
        
        # Verify ownership
        if voucher.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        
        data = request.get_json(silent=True) or {}
        
        # Get current allocation
        current_allocation = VoucherBudgetAllocation.query.filter_by(voucher_id=voucher_id).first()
        
        # Handle budget project changes
        new_budget_project_id = data.get('budget_project_id')
        new_amount = float(data.get('amount_due', voucher.total_amount)) if data.get('amount_due') else voucher.total_amount

        if not new_budget_project_id:
            return jsonify({
                'success': False,
                'message': 'Please select a budget project before saving the voucher'
            }), 400
        
        if current_allocation:
            # Check if budget project or amount changed
            if (int(new_budget_project_id) != current_allocation.budget_project_id or 
                new_amount != current_allocation.allocated_amount):
                
                # Restore the old budget
                old_budget_project = BudgetProject.query.get(current_allocation.budget_project_id)
                if old_budget_project:
                    old_budget_project.disbursed_amount -= current_allocation.allocated_amount
                    old_budget_project.remaining_balance = old_budget_project.total_budget - old_budget_project.disbursed_amount
                    old_budget_project.updated_at = datetime.utcnow()
                
                # Apply to new budget
                new_budget_project = BudgetProject.query.filter_by(
                    id=new_budget_project_id,
                    user_id=user_id,
                    is_active=True
                ).first()
                
                if not new_budget_project:
                    return jsonify({
                        'success': False,
                        'message': 'Budget project not found or inactive'
                    }), 404
                
                # Check if there's enough remaining balance (considering the restore)
                if new_amount > new_budget_project.remaining_balance:
                    return jsonify({
                        'success': False,
                        'message': f'OPS, SUMOBRA KA. Remaining balance: ₱{new_budget_project.remaining_balance:,.2f}'
                    }), 400
                
                # Update allocation
                current_allocation.budget_project_id = new_budget_project.id
                current_allocation.allocated_amount = new_amount
                
                # Deduct from new budget
                new_budget_project.disbursed_amount += new_amount
                new_budget_project.remaining_balance = new_budget_project.total_budget - new_budget_project.disbursed_amount
                new_budget_project.updated_at = datetime.utcnow()
        else:
            # Create new allocation for vouchers without existing allocation
            new_budget_project = BudgetProject.query.filter_by(
                id=new_budget_project_id,
                user_id=user_id,
                is_active=True
            ).first()
            
            if not new_budget_project:
                return jsonify({
                    'success': False,
                    'message': 'Budget project not found or inactive'
                }), 404
            
            if new_amount > new_budget_project.remaining_balance:
                return jsonify({
                    'success': False,
                    'message': f'OPS, SUMOBRA KA. Remaining balance: ₱{new_budget_project.remaining_balance:,.2f}'
                }), 400
            
            allocation = VoucherBudgetAllocation(
                voucher_id=voucher_id,
                budget_project_id=new_budget_project.id,
                allocated_amount=new_amount
            )
            db.session.add(allocation)
            
            new_budget_project.disbursed_amount += new_amount
            new_budget_project.remaining_balance = new_budget_project.total_budget - new_budget_project.disbursed_amount
            new_budget_project.updated_at = datetime.utcnow()
        
        # Update fields
        voucher.barangay = data.get('barangay', voucher.barangay)
        voucher.payee = data.get('payee', voucher.payee)
        voucher.address = data.get('address', voucher.address)
        voucher.tin = data.get('tin', voucher.tin)
        voucher.province = data.get('province', voucher.province)
        voucher.responsibility_center = data.get('responsibility_center', voucher.responsibility_center)
        voucher.fund_cluster = data.get('fund_cluster', voucher.fund_cluster)
        voucher.particulars = data.get('particulars', voucher.particulars)
        voucher.check_number = data.get('check_number', voucher.check_number)
        voucher.bank_name = data.get('bank_name', voucher.bank_name)
        voucher.or_number = data.get('or_number', voucher.or_number)
        
        if data.get('amount_due'):
            voucher.total_amount = new_amount
        
        if data.get('voucher_date'):
            try:
                voucher.voucher_date = datetime.fromisoformat(data['voucher_date']).date()
            except:
                pass
        
        if data.get('payment_date'):
            try:
                voucher.payment_date = datetime.fromisoformat(data['payment_date']).date()
            except:
                pass
        
        voucher.updated_at = datetime.utcnow()
        db.session.commit()

        remaining_budget = None
        allocation = VoucherBudgetAllocation.query.filter_by(voucher_id=voucher_id).first()
        if allocation:
            budget_project = BudgetProject.query.get(allocation.budget_project_id)
            if budget_project:
                remaining_budget = budget_project.remaining_balance
        
        return jsonify({
            'success': True,
            'message': 'Voucher updated successfully',
            'dv_number': voucher.dv_number,
            'voucher_id': voucher.id,
            'remaining_budget': remaining_budget
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/disbursement-vouchers', methods=['GET'])
def get_disbursement_vouchers():
    """Get all disbursement vouchers for current user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        vouchers = DisVoucher.query.filter_by(user_id=user_id).order_by(DisVoucher.created_at.desc()).all()
        
        result = []
        for v in vouchers:
            result.append({
                'id': v.id,
                'dv_number': v.dv_number,
                'payee': v.payee,
                'barangay': v.barangay,
                'amount_due': v.total_amount,
                'check_number': v.check_number,
                'bank_name': v.bank_name,
                'or_number': v.or_number,
                'status': v.status,
                'created_at': v.created_at.isoformat()
            })
        
        return jsonify({'success': True, 'vouchers': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/disbursement-voucher/<int:voucher_id>', methods=['GET'])
def get_disbursement_voucher(voucher_id):
    """Get a specific disbursement voucher"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        voucher = DisVoucher.query.get_or_404(voucher_id)
        
        # Verify ownership
        if voucher.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get budget allocation info
        allocation = VoucherBudgetAllocation.query.filter_by(voucher_id=voucher_id).first()
        budget_project_info = None
        
        if allocation:
            budget_project = BudgetProject.query.get(allocation.budget_project_id)
            if budget_project:
                budget_project_info = {
                    'id': budget_project.id,
                    'project_name': budget_project.project_name,
                    'fiscal_year': budget_project.fiscal_year,
                    'total_budget': budget_project.total_budget,
                    'disbursed_amount': budget_project.disbursed_amount,
                    'remaining_balance': budget_project.remaining_balance,
                    'allocated_amount': allocation.allocated_amount
                }
        
        return jsonify({
            'success': True,
            'voucher': {
                'id': voucher.id,
                'dv_number': voucher.dv_number,
                'barangay': voucher.barangay,
                'payee': voucher.payee,
                'address': voucher.address,
                'tin': voucher.tin,
                'province': voucher.province,
                'responsibility_center': voucher.responsibility_center,
                'fund_cluster': voucher.fund_cluster,
                'particulars': voucher.particulars,
                'amount_due': voucher.total_amount,
                'check_number': voucher.check_number,
                'bank_name': voucher.bank_name,
                'or_number': voucher.or_number,
                'payment_date': voucher.payment_date.isoformat() if voucher.payment_date else None,
                'status': voucher.status,
                'voucher_date': voucher.voucher_date.isoformat() if voucher.voucher_date else None,
                'created_at': voucher.created_at.isoformat(),
                'budget_project': budget_project_info
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/disbursement-voucher/<int:voucher_id>/mark-done', methods=['POST'])
def mark_voucher_done(voucher_id):
    """Mark a disbursement voucher as done/completed after printing"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        voucher = DisVoucher.query.get_or_404(voucher_id)
        
        # Verify ownership
        if voucher.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Mark as completed
        voucher.status = 'completed'
        voucher.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Voucher marked as completed',
            'status': 'completed'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/disbursement-voucher/<int:voucher_id>', methods=['DELETE'])
def delete_disbursement_voucher(voucher_id):
    """Delete a disbursement voucher"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        voucher = DisVoucher.query.get_or_404(voucher_id)
        
        # Verify ownership
        if voucher.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Restore budget allocation
        allocation = VoucherBudgetAllocation.query.filter_by(voucher_id=voucher_id).first()
        if allocation:
            budget_project = BudgetProject.query.get(allocation.budget_project_id)
            if budget_project:
                # Restore the disbursed amount back to the budget
                budget_project.disbursed_amount -= allocation.allocated_amount
                budget_project.remaining_balance = budget_project.total_budget - budget_project.disbursed_amount
                budget_project.updated_at = datetime.utcnow()
        
            # Delete the allocation record
            db.session.delete(allocation)
        
        # Delete associated line items
        DisVoucherLine.query.filter_by(voucher_id=voucher_id).delete()
        db.session.delete(voucher)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Voucher deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== Purchase Request Routes ====================

@app.route('/purchase-request')
def purchase_request_page():
    """Purchase Request page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    
    return render_template('purchase-request.html', profile=profile)


@app.route('/api/purchase-request', methods=['POST'])
def create_purchase_request():
    """Create a new purchase request"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        # Create purchase request
        pr = PurchaseRequest(
            user_id=user_id,
            pr_number=data.get('pr_number'),
            barangay=data.get('barangay'),
            municipality=data.get('municipality'),
            province=data.get('province'),
            pr_date=datetime.strptime(data.get('pr_date'), '%Y-%m-%d').date() if data.get('pr_date') else None,
            purpose=data.get('purpose'),
            total_amount=float(data.get('total_amount', 0)),
            requested_by=data.get('requested_by'),
            requested_by_position=data.get('requested_by_position'),
            requested_date=datetime.strptime(data.get('requested_date'), '%Y-%m-%d').date() if data.get('requested_date') else None,
            approved_by=data.get('approved_by'),
            approved_by_position=data.get('approved_by_position'),
            approved_date=datetime.strptime(data.get('approved_date'), '%Y-%m-%d').date() if data.get('approved_date') else None,
            status=data.get('status', 'draft')
        )
        
        db.session.add(pr)
        db.session.flush()  # Get the ID
        
        # Add line items
        items = data.get('items', [])
        for item in items:
            pr_item = PurchaseRequestItem(
                pr_id=pr.id,
                item_no=item.get('item_no'),
                quantity=float(item.get('quantity', 0)),
                unit_of_measurement=item.get('unit_of_measurement'),
                item_description=item.get('item_description'),
                estimated_unit_cost=float(item.get('estimated_unit_cost', 0)),
                estimated_amount=float(item.get('estimated_amount', 0))
            )
            db.session.add(pr_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Purchase request created successfully',
            'pr_id': pr.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/purchase-request/<int:pr_id>', methods=['GET'])
def get_purchase_request(pr_id):
    """Get a purchase request by ID"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        pr = PurchaseRequest.query.get_or_404(pr_id)
        
        # Verify ownership
        if pr.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get line items
        items = PurchaseRequestItem.query.filter_by(pr_id=pr_id).order_by(PurchaseRequestItem.item_no).all()
        
        return jsonify({
            'success': True,
            'purchase_request': {
                'id': pr.id,
                'pr_number': pr.pr_number,
                'barangay': pr.barangay,
                'municipality': pr.municipality,
                'province': pr.province,
                'pr_date': pr.pr_date.isoformat() if pr.pr_date else None,
                'purpose': pr.purpose,
                'total_amount': pr.total_amount,
                'requested_by': pr.requested_by,
                'requested_by_position': pr.requested_by_position,
                'requested_date': pr.requested_date.isoformat() if pr.requested_date else None,
                'approved_by': pr.approved_by,
                'approved_by_position': pr.approved_by_position,
                'approved_date': pr.approved_date.isoformat() if pr.approved_date else None,
                'status': pr.status,
                'created_at': pr.created_at.isoformat()
            },
            'items': [{
                'id': item.id,
                'item_no': item.item_no,
                'quantity': item.quantity,
                'unit_of_measurement': item.unit_of_measurement,
                'item_description': item.item_description,
                'estimated_unit_cost': item.estimated_unit_cost,
                'estimated_amount': item.estimated_amount
            } for item in items]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/purchase-request/<int:pr_id>', methods=['PUT'])
def update_purchase_request(pr_id):
    """Update a purchase request"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        pr = PurchaseRequest.query.get_or_404(pr_id)
        
        # Verify ownership
        if pr.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Update purchase request
        pr.pr_number = data.get('pr_number', pr.pr_number)
        pr.barangay = data.get('barangay', pr.barangay)
        pr.municipality = data.get('municipality', pr.municipality)
        pr.province = data.get('province', pr.province)
        pr.pr_date = datetime.strptime(data.get('pr_date'), '%Y-%m-%d').date() if data.get('pr_date') else pr.pr_date
        pr.purpose = data.get('purpose', pr.purpose)
        pr.total_amount = float(data.get('total_amount', pr.total_amount))
        pr.requested_by = data.get('requested_by', pr.requested_by)
        pr.requested_by_position = data.get('requested_by_position', pr.requested_by_position)
        pr.requested_date = datetime.strptime(data.get('requested_date'), '%Y-%m-%d').date() if data.get('requested_date') else pr.requested_date
        pr.approved_by = data.get('approved_by', pr.approved_by)
        pr.approved_by_position = data.get('approved_by_position', pr.approved_by_position)
        pr.approved_date = datetime.strptime(data.get('approved_date'), '%Y-%m-%d').date() if data.get('approved_date') else pr.approved_date
        pr.status = data.get('status', pr.status)
        pr.updated_at = datetime.utcnow()
        
        # Delete existing items and add new ones
        PurchaseRequestItem.query.filter_by(pr_id=pr_id).delete()
        
        items = data.get('items', [])
        for item in items:
            pr_item = PurchaseRequestItem(
                pr_id=pr.id,
                item_no=item.get('item_no'),
                quantity=float(item.get('quantity', 0)),
                unit_of_measurement=item.get('unit_of_measurement'),
                item_description=item.get('item_description'),
                estimated_unit_cost=float(item.get('estimated_unit_cost', 0)),
                estimated_amount=float(item.get('estimated_amount', 0))
            )
            db.session.add(pr_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Purchase request updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/purchase-request/<int:pr_id>', methods=['DELETE'])
def delete_purchase_request(pr_id):
    """Delete a purchase request"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        pr = PurchaseRequest.query.get_or_404(pr_id)
        
        # Verify ownership
        if pr.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Delete associated line items
        PurchaseRequestItem.query.filter_by(pr_id=pr_id).delete()
        db.session.delete(pr)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Purchase request deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/purchase-requests', methods=['GET'])
def get_purchase_requests():
    """Get all purchase requests for the current user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        prs = PurchaseRequest.query.filter_by(user_id=user_id).order_by(PurchaseRequest.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'purchase_requests': [{
                'id': pr.id,
                'pr_number': pr.pr_number,
                'barangay': pr.barangay,
                'municipality': pr.municipality,
                'province': pr.province,
                'pr_date': pr.pr_date.isoformat() if pr.pr_date else None,
                'total_amount': pr.total_amount,
                'status': pr.status,
                'created_at': pr.created_at.isoformat()
            } for pr in prs]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Canvass Routes (Request for Price Quotation)
@app.route('/canvass')
def canvass_page():
    """Canvass page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    
    return render_template('canvass.html', profile=profile)


@app.route('/api/canvass', methods=['POST'])
def create_canvass():
    """Create a new canvass"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        # Create canvass
        canvass = Canvass(
            user_id=user_id,
            pr_number=data.get('pr_number'),
            canvass_date=datetime.strptime(data.get('canvass_date'), '%Y-%m-%d').date() if data.get('canvass_date') else None,
            fod=data.get('fod'),
            delivery_days=int(data.get('delivery_days', 0)),
            total_amount=float(data.get('total_amount', 0)),
            canvassed_by=data.get('canvassed_by'),
            canvassed_date=datetime.strptime(data.get('canvassed_date'), '%Y-%m-%d').date() if data.get('canvassed_date') else None,
            status=data.get('status', 'draft')
        )
        
        db.session.add(canvass)
        db.session.flush()  # Get the ID
        
        # Add line items
        items = data.get('items', [])
        for item in items:
            canvass_item = CanvassItem(
                canvass_id=canvass.id,
                item_no=item.get('item_no'),
                quantity=float(item.get('quantity', 0)),
                unit=item.get('unit'),
                articles=item.get('articles'),
                unit_price=float(item.get('unit_price', 0)),
                total=float(item.get('total', 0))
            )
            db.session.add(canvass_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Canvass created successfully',
            'canvass_id': canvass.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/canvass/<int:canvass_id>', methods=['GET'])
def get_canvass(canvass_id):
    """Get a canvass by ID"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        canvass = Canvass.query.get_or_404(canvass_id)
        
        # Verify ownership
        if canvass.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get line items
        items = CanvassItem.query.filter_by(canvass_id=canvass_id).order_by(CanvassItem.item_no).all()
        
        return jsonify({
            'success': True,
            'canvass': {
                'id': canvass.id,
                'pr_number': canvass.pr_number,
                'canvass_date': canvass.canvass_date.isoformat() if canvass.canvass_date else None,
                'fod': canvass.fod,
                'delivery_days': canvass.delivery_days,
                'total_amount': canvass.total_amount,
                'canvassed_by': canvass.canvassed_by,
                'canvassed_date': canvass.canvassed_date.isoformat() if canvass.canvassed_date else None,
                'status': canvass.status,
                'created_at': canvass.created_at.isoformat()
            },
            'items': [{
                'id': item.id,
                'item_no': item.item_no,
                'quantity': item.quantity,
                'unit': item.unit,
                'articles': item.articles,
                'unit_price': item.unit_price,
                'total': item.total
            } for item in items]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/canvass/<int:canvass_id>', methods=['PUT'])
def update_canvass(canvass_id):
    """Update a canvass"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        canvass = Canvass.query.get_or_404(canvass_id)
        
        # Verify ownership
        if canvass.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Update canvass
        canvass.pr_number = data.get('pr_number', canvass.pr_number)
        canvass.canvass_date = datetime.strptime(data.get('canvass_date'), '%Y-%m-%d').date() if data.get('canvass_date') else canvass.canvass_date
        canvass.fod = data.get('fod', canvass.fod)
        canvass.delivery_days = int(data.get('delivery_days', canvass.delivery_days))
        canvass.total_amount = float(data.get('total_amount', canvass.total_amount))
        canvass.canvassed_by = data.get('canvassed_by', canvass.canvassed_by)
        canvass.canvassed_date = datetime.strptime(data.get('canvassed_date'), '%Y-%m-%d').date() if data.get('canvassed_date') else canvass.canvassed_date
        canvass.status = data.get('status', canvass.status)
        canvass.updated_at = datetime.utcnow()
        
        # Delete existing items and add new ones
        CanvassItem.query.filter_by(canvass_id=canvass_id).delete()
        
        items = data.get('items', [])
        for item in items:
            canvass_item = CanvassItem(
                canvass_id=canvass.id,
                item_no=item.get('item_no'),
                quantity=float(item.get('quantity', 0)),
                unit=item.get('unit'),
                articles=item.get('articles'),
                unit_price=float(item.get('unit_price', 0)),
                total=float(item.get('total', 0))
            )
            db.session.add(canvass_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Canvass updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/canvass/<int:canvass_id>', methods=['DELETE'])
def delete_canvass(canvass_id):
    """Delete a canvass"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        canvass = Canvass.query.get_or_404(canvass_id)
        
        # Verify ownership
        if canvass.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Delete associated line items
        CanvassItem.query.filter_by(canvass_id=canvass_id).delete()
        db.session.delete(canvass)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Canvass deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/canvasses', methods=['GET'])
def get_canvasses():
    """Get all canvasses for the current user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        canvasses = Canvass.query.filter_by(user_id=user_id).order_by(Canvass.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'canvasses': [{
                'id': c.id,
                'pr_number': c.pr_number,
                'canvass_date': c.canvass_date.isoformat() if c.canvass_date else None,
                'fod': c.fod,
                'total_amount': c.total_amount,
                'status': c.status,
                'created_at': c.created_at.isoformat()
            } for c in canvasses]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    init_db()
    # Production settings
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
