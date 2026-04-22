from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import os
import re
import logging
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ctf_platform.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'void-protocol-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ctf.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    solves = db.relationship('Solve', backref='user', lazy=True)

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    flag = db.Column(db.String(255), nullable=False, unique=True)
    file_path = db.Column(db.String(255), nullable=False)
    is_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    solves = db.relationship('Solve', backref='challenge', lazy=True)

class Solve(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    flag = db.Column(db.String(255), nullable=False)
    points_earned = db.Column(db.Integer, nullable=False)
    bonus_points = db.Column(db.Integer, default=0)
    solved_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    flag = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# IDOR Challenge Models
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='open')
    priority = db.Column(db.String(50), default='normal')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_admin_ticket = db.Column(db.Boolean, default=False)

class PayrollRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    is_executive = db.Column(db.Boolean, default=False)

class CloudFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, unique=True, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    owner_id = db.Column(db.Integer, nullable=False)
    is_confidential = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class ApiProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), default='user')
    meta_data = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, unique=True, nullable=False)
    customer_id = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    items = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    notes = db.Column(db.Text)
    is_internal = db.Column(db.Boolean, default=False)

# Advanced IDOR Challenge Models
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    team_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='active')
    documents = db.Column(db.Text)
    is_restricted = db.Column(db.Boolean, default=False)

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, unique=True, nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    diagnosis = db.Column(db.Text)
    treatment = db.Column(db.Text)
    doctor_notes = db.Column(db.Text)
    admission_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_sensitive = db.Column(db.Boolean, default=False)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    items = db.Column(db.Text)
    invoice_metadata = db.Column(db.Text)
    is_confidential = db.Column(db.Boolean, default=False)

class MessageThread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, unique=True, nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    participants = db.Column(db.Text)
    messages = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_admin_thread = db.Column(db.Boolean, default=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    project = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(50), default='normal')
    status = db.Column(db.String(50), default='open')
    assignee = db.Column(db.String(100))
    is_internal = db.Column(db.Boolean, default=False)

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_admin:
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def not_banned(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
            if user and user.is_banned:
                session.clear()
                return redirect(url_for('login', banned=True))
        return f(*args, **kwargs)
    return decorated_function

# Helper functions
def calculate_bonus_points(challenge_id, solve_order):
    """Calculate bonus points based on solve order (first solver gets highest bonus)"""
    base_bonus = 50
    if solve_order == 1:
        return base_bonus
    elif solve_order <= 3:
        return base_bonus // 2
    elif solve_order <= 5:
        return base_bonus // 4
    elif solve_order <= 10:
        return base_bonus // 8
    return 0

def initialize_challenges():
    """Initialize challenges from existing HTML files"""
    logger.info("Initializing challenges...")
    
    # IDOR Challenges
    idor_challenges = [
        {
            'title': 'Internal Ticket System',
            'description': 'An internal support ticket system with predictable user identifiers. The API endpoint accepts user_id parameters without proper authorization checks.',
            'category': 'IDOR',
            'points': 100,
            'difficulty': 'easy',
            'flag': 'flag{idor_ticket_system_breach}',
            'file_path': 'challenge-idor-1-ticket-system.html'
        },
        {
            'title': 'Employee Payroll Portal',
            'description': 'A payroll management system with structured employee IDs. Access executive records by enumerating through the predictable ID pattern.',
            'category': 'IDOR',
            'points': 120,
            'difficulty': 'easy',
            'flag': 'flag{idor_payroll_executive_access}',
            'file_path': 'challenge-idor-2-payroll.html'
        },
        {
            'title': 'Cloud Storage Viewer',
            'description': 'A document storage system with file indexing patterns. Enumerate file IDs to access confidential documents.',
            'category': 'IDOR',
            'points': 130,
            'difficulty': 'medium',
            'flag': 'flag{idor_cloud_file_breach}',
            'file_path': 'challenge-idor-3-cloud-storage.html'
        },
        {
            'title': 'API Profile Viewer',
            'description': 'A user profile API with predictable endpoints. Access administrative profiles by modifying the profile ID.',
            'category': 'IDOR',
            'points': 140,
            'difficulty': 'medium',
            'flag': 'flag{idor_api_profile_breach}',
            'file_path': 'challenge-idor-4-api-profile.html'
        },
        {
            'title': 'Order Management System',
            'description': 'An order processing system with sequential order IDs. Access internal orders by enumerating through the order sequence.',
            'category': 'IDOR',
            'points': 150,
            'difficulty': 'medium',
            'flag': 'flag{idor_order_system_breach}',
            'file_path': 'challenge-idor-5-orders.html'
        }
    ]
    
    for chal in idor_challenges:
        existing = Challenge.query.filter_by(flag=chal['flag']).first()
        if not existing:
            challenge = Challenge(**chal)
            db.session.add(challenge)
            logger.info(f"Added IDOR challenge: {chal['title']}")
        else:
            logger.info(f"Challenge already exists: {chal['title']}")
    
    # Cookie-Based Challenges
    cookie_challenges = [
        {
            'title': 'Role-Based Cookie Manipulation',
            'description': 'A dashboard system that handles user roles via client-side cookies. Manipulate the role cookie to escalate privileges.',
            'category': 'Cookie',
            'points': 100,
            'difficulty': 'easy',
            'flag': 'flag{cookie_role_escalation_success}',
            'file_path': 'challenge-cookie-1-role.html'
        },
        {
            'title': 'Base64 Encoded Session Cookie',
            'description': 'A system with Base64 encoded session data. Decode, modify, and re-encode the cookie to gain admin access.',
            'category': 'Cookie',
            'points': 130,
            'difficulty': 'medium',
            'flag': 'flag{base64_cookie_manipulation_success}',
            'file_path': 'challenge-cookie-2-base64.html'
        },
        {
            'title': 'Cookie Integrity Flaw',
            'description': 'A login-protected panel with inconsistent cookie validation logic. Exploit the flawed authorization check.',
            'category': 'Cookie',
            'points': 140,
            'difficulty': 'medium',
            'flag': 'flag{cookie_integrity_flaw_success}',
            'file_path': 'challenge-cookie-3-integrity.html'
        },
        {
            'title': 'JWT Misconfiguration',
            'description': 'A system using JWT tokens stored in cookies without signature verification. Modify the payload to escalate privileges.',
            'category': 'Cookie',
            'points': 160,
            'difficulty': 'hard',
            'flag': 'flag{jwt_misconfiguration_success}',
            'file_path': 'challenge-cookie-4-jwt.html'
        },
        {
            'title': 'Hidden Cookie Behavior',
            'description': 'A theme settings panel with hidden functionality triggered by specific cookie values. Discover the hidden behavior.',
            'category': 'Cookie',
            'points': 110,
            'difficulty': 'easy',
            'flag': 'flag{hidden_cookie_behavior_success}',
            'file_path': 'challenge-cookie-5-hidden.html'
        }
    ]
    
    for chal in cookie_challenges:
        existing = Challenge.query.filter_by(flag=chal['flag']).first()
        if not existing:
            challenge = Challenge(**chal)
            db.session.add(challenge)
            logger.info(f"Added Cookie challenge: {chal['title']}")
        else:
            logger.info(f"Challenge already exists: {chal['title']}")
    
    # Hybrid Challenge
    hybrid_challenge = {
        'title': 'Admin Panel Breach',
        'description': 'An advanced challenge requiring both IDOR exploitation and cookie manipulation to breach the admin panel.',
        'category': 'Hybrid',
        'points': 200,
        'difficulty': 'hard',
        'flag': 'flag{hybrid_admin_breach_success}',
        'file_path': 'challenge-hybrid-admin-breach.html'
    }
    
    existing = Challenge.query.filter_by(flag=hybrid_challenge['flag']).first()
    if not existing:
        challenge = Challenge(**hybrid_challenge)
        db.session.add(challenge)
        logger.info(f"Added Hybrid challenge: {hybrid_challenge['title']}")
    else:
        logger.info(f"Challenge already exists: {hybrid_challenge['title']}")
    
    # Advanced IDOR Challenges
    advanced_idor_challenges = [
        {
            'title': 'Project Collaboration Workspace',
            'description': 'A project management system where users access shared projects by team ID. Discover your team_id via profile API, then enumerate other team IDs to access restricted workspaces.',
            'category': 'IDOR',
            'points': 180,
            'difficulty': 'medium',
            'flag': 'flag{project_workspace_breach}',
            'file_path': 'challenge-idor-6-projects.html'
        },
        {
            'title': 'Medical Records Portal',
            'description': 'A patient records system with randomly distributed but partially predictable record IDs. Observe patterns (gaps, increments) to find high-privilege records.',
            'category': 'IDOR',
            'points': 190,
            'difficulty': 'medium',
            'flag': 'flag{medical_records_breach}',
            'file_path': 'challenge-idor-7-medical.html'
        },
        {
            'title': 'Invoice Management API',
            'description': 'An invoice system with structured invoice IDs following the format INV-[YEAR]-[NUMBER]. Understand the pattern and modify the last digits to access confidential invoices.',
            'category': 'IDOR',
            'points': 200,
            'difficulty': 'medium',
            'flag': 'flag{invoice_management_breach}',
            'file_path': 'challenge-idor-8-invoices.html'
        },
        {
            'title': 'Private Messaging System',
            'description': 'A messaging system where threads belong to multiple users. Access control only checks login, not thread ownership. Enumerate thread IDs to find admin conversations.',
            'category': 'IDOR',
            'points': 210,
            'difficulty': 'medium',
            'flag': 'flag{messaging_system_breach}',
            'file_path': 'challenge-idor-9-messages.html'
        },
        {
            'title': 'Task Management Board',
            'description': 'A task management system with projects identified by name. Hidden projects exist (beta, internal, admin). Guess project names based on hints to access internal tasks.',
            'category': 'IDOR',
            'points': 220,
            'difficulty': 'medium',
            'flag': 'flag{task_management_breach}',
            'file_path': 'challenge-idor-10-tasks.html'
        }
    ]
    
    for chal in advanced_idor_challenges:
        existing = Challenge.query.filter_by(flag=chal['flag']).first()
        if not existing:
            challenge = Challenge(**chal)
            db.session.add(challenge)
            logger.info(f"Added Advanced IDOR challenge: {chal['title']}")
        else:
            logger.info(f"Challenge already exists: {chal['title']}")
    
    # Advanced Cookie Challenges
    advanced_cookie_challenges = [
        {
            'title': 'Multi-Field Cookie Manipulation',
            'description': 'A session system with multiple cookies (user_id, role, access_level). All fields must align for admin access. Modify cookies consistently to elevate privileges.',
            'category': 'Cookie',
            'points': 180,
            'difficulty': 'medium',
            'flag': 'flag{multi_field_cookie_success}',
            'file_path': 'challenge-cookie-6-multi-field.html'
        },
        {
            'title': 'Signed Cookie (Weak Validation)',
            'description': 'A system with signed cookies (data + signature). Signature validation is weak and only checks if the signature is numeric. Modify data and bypass signature logic.',
            'category': 'Cookie',
            'points': 200,
            'difficulty': 'medium',
            'flag': 'flag{weak_signature_bypass_success}',
            'file_path': 'challenge-cookie-7-signed.html'
        },
        {
            'title': 'Time-Based Cookie Access',
            'description': 'A session system with timestamp-based access control. Manipulate the timestamp value to unlock privileged session access.',
            'category': 'Cookie',
            'points': 190,
            'difficulty': 'medium',
            'flag': 'flag{time_based_cookie_success}',
            'file_path': 'challenge-cookie-8-time.html'
        },
        {
            'title': 'Nested Encoding Cookie',
            'description': 'A session system with double-encoded cookies (Base64 → JSON → Base64). Decode multiple layers, modify the role, and re-encode correctly.',
            'category': 'Cookie',
            'points': 210,
            'difficulty': 'medium',
            'flag': 'flag{nested_encoding_success}',
            'file_path': 'challenge-cookie-9-nested.html'
        },
        {
            'title': 'Feature Flag Cookie',
            'description': 'A system with feature flags controlled by cookies. Hidden features exist (admin_panel, debug_mode). Enable hidden features to access restricted functionality.',
            'category': 'Cookie',
            'points': 170,
            'difficulty': 'medium',
            'flag': 'flag{feature_flag_success}',
            'file_path': 'challenge-cookie-10-features.html'
        }
    ]
    
    for chal in advanced_cookie_challenges:
        existing = Challenge.query.filter_by(flag=chal['flag']).first()
        if not existing:
            challenge = Challenge(**chal)
            db.session.add(challenge)
            logger.info(f"Added Advanced Cookie challenge: {chal['title']}")
        else:
            logger.info(f"Challenge already exists: {chal['title']}")
    
    # Advanced Hybrid Challenge
    advanced_hybrid_challenge = {
        'title': 'Secure API Gateway Breach',
        'description': 'An advanced challenge requiring both IDOR exploitation (API endpoint data access) and cookie manipulation (session control). Combine both vulnerabilities logically to achieve full access.',
        'category': 'Hybrid',
        'points': 250,
        'difficulty': 'medium',
        'flag': 'flag{hybrid_api_gateway_success}',
        'file_path': 'challenge-hybrid-2-api-gateway.html'
    }
    
    existing = Challenge.query.filter_by(flag=advanced_hybrid_challenge['flag']).first()
    if not existing:
        challenge = Challenge(**advanced_hybrid_challenge)
        db.session.add(challenge)
        logger.info(f"Added Advanced Hybrid challenge: {advanced_hybrid_challenge['title']}")
    else:
        logger.info(f"Challenge already exists: {advanced_hybrid_challenge['title']}")
    
    db.session.commit()
    logger.info(f"Total challenges in database: {Challenge.query.count()}")

def create_default_admin():
    """Create default admin account"""
    admin = User.query.filter_by(username='GuildMaster').first()
    if not admin:
        admin = User(
            username='GuildMaster',
            email='admin@voidprotocol.ctf',
            password_hash=generate_password_hash('arcaneallure333666404*'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

def initialize_idor_challenge_data():
    """Initialize sample data for IDOR challenges"""
    logger.info("Initializing IDOR challenge data...")
    
    # Tickets data
    if Ticket.query.count() == 0:
        # User tickets
        for i in range(1000, 1005):
            ticket = Ticket(
                user_id=i,
                title=f'Support Ticket #{i}',
                description=f'User {i} is experiencing login issues',
                status='open',
                priority='normal'
            )
            db.session.add(ticket)
        
        # Admin ticket with flag
        admin_ticket = Ticket(
            user_id=1,
            title='Critical Security Advisory',
            description='flag{idor_ticket_system_breach} - Review this security incident immediately',
            status='open',
            priority='critical',
            is_admin_ticket=True
        )
        db.session.add(admin_ticket)
        logger.info("Added tickets data")
    
    # Payroll data
    if PayrollRecord.query.count() == 0:
        for i in range(100, 110):
            record = PayrollRecord(
                employee_id=f'EMP{i}',
                name=f'Employee {i}',
                department='Engineering',
                position='Developer',
                salary=75000,
                notes='Regular employee'
            )
            db.session.add(record)
        
        # Executive record with flag
        exec_record = PayrollRecord(
            employee_id='EMP999',
            name='Chief Executive Officer',
            department='Executive',
            position='CEO',
            salary=500000,
            notes='flag{idor_payroll_executive_access} - Confidential executive compensation data'
        )
        db.session.add(exec_record)
        logger.info("Added payroll data")
    
    # Cloud files data
    if CloudFile.query.count() == 0:
        for i in range(7800, 7810):
            file = CloudFile(
                file_id=i,
                filename=f'document_{i}.txt',
                content=f'This is document {i} content',
                owner_id=1000,
                is_confidential=False
            )
            db.session.add(file)
        
        # Confidential file with flag
        confidential_file = CloudFile(
            file_id=9999,
            filename='confidential_strategic_plan.txt',
            content='flag{idor_cloud_file_breach} - Q4 Strategic Plan: Expand market penetration by 40%',
            owner_id=1,
            is_confidential=True
        )
        db.session.add(confidential_file)
        logger.info("Added cloud files data")
    
    # API profiles data
    if ApiProfile.query.count() == 0:
        for i in range(240, 250):
            profile = ApiProfile(
                profile_id=i,
                username=f'user_{i}',
                email=f'user{i}@example.com',
                role='user',
                meta_data='Standard user account'
            )
            db.session.add(profile)
        
        # Admin profile with flag
        admin_profile = ApiProfile(
            profile_id=999,
            username='admin_user',
            email='admin@system.internal',
            role='admin',
            meta_data='flag{idor_api_profile_breach} - System administrator with full access'
        )
        db.session.add(admin_profile)
        logger.info("Added API profiles data")
    
    # Orders data
    if Order.query.count() == 0:
        for i in range(55600, 55610):
            order = Order(
                order_id=i,
                customer_id=1000,
                customer_name=f'Customer {i}',
                items='Standard product package',
                total_amount=99.99,
                status='shipped',
                notes='Regular order'
            )
            db.session.add(order)
        
        # Internal order with flag
        internal_order = Order(
            order_id=99999,
            customer_id=1,
            customer_name='Internal Procurement',
            items='Security audit services',
            total_amount=15000.00,
            status='pending',
            notes='flag{idor_order_system_breach} - Internal security audit order - Do not process without approval'
        )
        db.session.add(internal_order)
        logger.info("Added orders data")
    
    db.session.commit()
    logger.info("IDOR challenge data initialization complete")

def initialize_advanced_challenge_data():
    """Initialize sample data for advanced IDOR challenges"""
    logger.info("Initializing advanced challenge data...")
    
    # Projects data
    if Project.query.count() == 0:
        # User projects for team 45
        for i in range(100, 105):
            project = Project(
                project_id=i,
                name=f'Project {i}',
                description=f'Team project for development team',
                team_id=45,
                status='active',
                documents='Standard project documentation'
            )
            db.session.add(project)
        
        # Admin team project with flag
        admin_project = Project(
            project_id=999,
            name='Restricted Admin Workspace',
            description='flag{project_workspace_breach} - Internal administrative project workspace. Do not access without authorization.',
            team_id=1,
            status='active',
            documents='Confidential administrative documents',
            is_restricted=True
        )
        db.session.add(admin_project)
        logger.info("Added projects data")
    
    # Medical records data
    if MedicalRecord.query.count() == 0:
        # Random distribution with gaps
        record_ids = [8821, 8825, 8830, 8842, 8850, 8900, 8950, 9000]
        for rid in record_ids:
            record = MedicalRecord(
                record_id=rid,
                patient_name=f'Patient {rid}',
                diagnosis='Routine checkup',
                treatment='Standard treatment',
                doctor_notes='Patient in stable condition',
                is_sensitive=False
            )
            db.session.add(record)
        
        # Admin/test account record with flag
        admin_record = MedicalRecord(
            record_id=9999,
            patient_name='System Administrator',
            diagnosis='flag{medical_records_breach} - Test account for system verification. Access restricted.',
            treatment='Monitoring and maintenance',
            doctor_notes='flag{medical_records_breach} - This is a privileged account record.',
            is_sensitive=True
        )
        db.session.add(admin_record)
        logger.info("Added medical records data")
    
    # Invoices data
    if Invoice.query.count() == 0:
        for i in range(1040, 1050):
            invoice = Invoice(
                invoice_number=f'INV-2026-{i}',
                client_name=f'Client {i}',
                amount=1500.00,
                status='paid',
                items='Standard services',
                invoice_metadata='Regular invoice',
                is_confidential=False
            )
            db.session.add(invoice)
        
        # Confidential invoice with flag
        confidential_invoice = Invoice(
            invoice_number='INV-2026-9999',
            client_name='Internal Procurement',
            amount=50000.00,
            status='pending',
            items='Security audit and consulting',
            invoice_metadata='flag{invoice_management_breach} - CONFIDENTIAL: Internal security audit invoice. Do not process without approval.',
            is_confidential=True
        )
        db.session.add(confidential_invoice)
        logger.info("Added invoices data")
    
    # Message threads data
    if MessageThread.query.count() == 0:
        for i in range(335, 345):
            thread = MessageThread(
                thread_id=i,
                subject=f'Thread {i} - Project Discussion',
                participants='user1, user2, user3',
                messages='Standard project communication',
                is_admin_thread=False
            )
            db.session.add(thread)
        
        # Admin thread with flag
        admin_thread = MessageThread(
            thread_id=999,
            subject='flag{messaging_system_breach} - Critical Security Discussion',
            participants='admin, security_team, executives',
            messages='flag{messaging_system_breach} - This thread contains sensitive security information and incident response details.',
            is_admin_thread=True
        )
        db.session.add(admin_thread)
        logger.info("Added message threads data")
    
    # Tasks data
    if Task.query.count() == 0:
        # Alpha project tasks
        for i in range(200, 210):
            task = Task(
                task_id=i,
                title=f'Task {i}',
                description='Standard development task',
                project='alpha',
                priority='normal',
                status='open',
                assignee='developer'
            )
            db.session.add(task)
        
        # Internal project task with flag
        internal_task = Task(
            task_id=999,
            title='flag{task_management_breach} - Critical Security Review',
            description='flag{task_management_breach} - Internal security review task. High priority. Complete immediately.',
            project='internal',
            priority='critical',
            status='open',
            assignee='security_admin',
            is_internal=True
        )
        db.session.add(internal_task)
        logger.info("Added tasks data")
    
    db.session.commit()
    logger.info("Advanced challenge data initialization complete")

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/register', methods=['POST'])
def register():
    logger.info("Registration attempt")
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        logger.info(f"Registration for username: {username}, email: {email}")
        
        if not username or not email or not password:
            logger.warning("Registration failed: Missing fields")
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        if len(username) < 3:
            logger.warning(f"Registration failed: Username too short: {username}")
            return jsonify({'success': False, 'message': 'Username must be at least 3 characters'})
        
        if len(password) < 6:
            logger.warning(f"Registration failed: Password too short for user: {username}")
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'})
        
        if User.query.filter_by(username=username).first():
            logger.warning(f"Registration failed: Username already exists: {username}")
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        if User.query.filter_by(email=email).first():
            logger.warning(f"Registration failed: Email already registered: {email}")
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        logger.info(f"Registration successful for user: {username} (ID: {user.id})")
        return jsonify({'success': True, 'message': 'Registration successful'})
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    banned = request.args.get('banned', False)
    if request.method == 'POST':
        logger.info("Login attempt")
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            logger.info(f"Login attempt for username: {username}")
            
            user = User.query.filter_by(username=username).first()
            
            if not user or not check_password_hash(user.password_hash, password):
                logger.warning(f"Login failed: Invalid credentials for username: {username}")
                return render_template('landing.html', login_error='Invalid credentials')
            
            if user.is_banned:
                logger.warning(f"Login denied: User {username} is banned")
                return render_template('landing.html', login_error='Account has been banned')
            
            session['user_id'] = user.id
            logger.info(f"Login successful for user: {username} (ID: {user.id})")
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return render_template('landing.html', login_error='Login failed. Please try again.')
    
    return render_template('landing.html', banned=banned)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
@not_banned
def dashboard():
    logger.info("Loading dashboard")
    try:
        user = db.session.get(User, session['user_id'])
        if not user:
            logger.error(f"User not found in session: {session.get('user_id')}")
            return redirect(url_for('logout'))
        
        total_challenges = Challenge.query.filter_by(is_enabled=True).count()
        solved_challenges = Solve.query.filter_by(user_id=user.id).count()
        recent_solves = Solve.query.filter_by(user_id=user.id).order_by(Solve.solved_at.desc()).limit(5).all()
        
        logger.info(f"Dashboard loaded for user {user.username}")
        return render_template('dashboard.html', user=user, total_challenges=total_challenges, 
                              solved_challenges=solved_challenges, recent_solves=recent_solves)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}", exc_info=True)
        return render_template('dashboard.html', user=user, total_challenges=0, 
                              solved_challenges=0, recent_solves=[])

@app.route('/challenges')
@login_required
@not_banned
def challenges():
    logger.info("Fetching challenges list")
    try:
        user = db.session.get(User, session['user_id'])
        if not user:
            logger.error(f"User not found in session: {session.get('user_id')}")
            return redirect(url_for('logout'))
        
        all_challenges = Challenge.query.filter_by(is_enabled=True).all()
        user_solved = {s.challenge_id for s in Solve.query.filter_by(user_id=user.id).all()}
        
        challenges_with_status = []
        for challenge in all_challenges:
            is_solved = challenge.id in user_solved
            challenges_with_status.append({
                'challenge': challenge,
                'is_solved': is_solved
            })
        
        logger.info(f"Returning {len(challenges_with_status)} challenges for user {user.username}")
        return render_template('challenges.html', user=user, challenges=challenges_with_status)
    except Exception as e:
        logger.error(f"Error fetching challenges: {str(e)}", exc_info=True)
        return render_template('challenges.html', user=user, challenges=[])

@app.route('/challenge/<int:challenge_id>')
@login_required
@not_banned
def view_challenge(challenge_id):
    logger.info(f"Viewing challenge {challenge_id}")
    try:
        user = db.session.get(User, session['user_id'])
        if not user:
            logger.error(f"User not found in session: {session.get('user_id')}")
            return redirect(url_for('logout'))
        
        challenge = db.session.get(Challenge, challenge_id)
        if not challenge:
            logger.error(f"Challenge not found: {challenge_id}")
            return redirect(url_for('challenges'))
        
        if not challenge.is_enabled:
            logger.warning(f"Challenge {challenge_id} is disabled")
            return redirect(url_for('challenges'))
        
        is_solved = Solve.query.filter_by(user_id=user.id, challenge_id=challenge_id).first() is not None
        
        logger.info(f"Rendering challenge {challenge.title} for user {user.username}")
        return render_template('view_challenge.html', user=user, challenge=challenge, is_solved=is_solved)
    except Exception as e:
        logger.error(f"Error viewing challenge {challenge_id}: {str(e)}", exc_info=True)
        return redirect(url_for('challenges'))

@app.route('/challenge-file/<path:filename>')
@login_required
@not_banned
def serve_challenge_file(filename):
    return send_from_directory('.', filename)

@app.route('/submit-flag', methods=['POST'])
@login_required
@not_banned
def submit_flag():
    logger.info("=== Flag Submission Started ===")
    user = db.session.get(User, session['user_id'])
    challenge_id = request.form.get('challenge_id')
    flag = request.form.get('flag', '').strip()
    
    logger.info(f"User: {user.username if user else 'Unknown'} (ID: {session.get('user_id')})")
    logger.info(f"Challenge ID: {challenge_id}")
    logger.info(f"Submitted flag: {flag}")
    
    if not challenge_id or not flag:
        logger.warning("Missing challenge or flag in submission")
        return jsonify({'success': False, 'message': 'Missing challenge or flag'})
    
    challenge = db.session.get(Challenge, challenge_id)
    if not challenge:
        logger.error(f"Challenge not found: {challenge_id}")
        return jsonify({'success': False, 'message': 'Challenge not found'})
    
    logger.info(f"Challenge found: {challenge.title}")
    logger.info(f"Expected flag: {challenge.flag}")
    
    # Check if already solved
    existing_solve = Solve.query.filter_by(user_id=user.id, challenge_id=challenge_id).first()
    if existing_solve:
        logger.warning(f"User {user.username} already solved challenge {challenge.title}")
        return jsonify({'success': False, 'message': 'Challenge already solved'})
    
    # Record submission (always log for debugging)
    is_correct = (flag == challenge.flag)
    logger.info(f"Flag comparison: {'CORRECT' if is_correct else 'INCORRECT'}")
    
    submission = Submission(
        user_id=user.id,
        challenge_id=challenge_id,
        flag=flag,
        is_correct=is_correct
    )
    db.session.add(submission)
    
    if flag == challenge.flag:
        # Calculate solve order for bonus
        solve_count = Solve.query.filter_by(challenge_id=challenge_id).count()
        solve_order = solve_count + 1
        bonus_points = calculate_bonus_points(challenge_id, solve_order)
        total_points = challenge.points + bonus_points
        
        logger.info(f"Correct flag! Solve order: {solve_order}, Bonus: {bonus_points}, Total: {total_points}")
        
        # Record solve
        solve = Solve(
            user_id=user.id,
            challenge_id=challenge_id,
            flag=flag,
            points_earned=challenge.points,
            bonus_points=bonus_points
        )
        db.session.add(solve)
        
        # Update user score
        user.score += total_points
        db.session.commit()
        
        logger.info(f"User {user.username} score updated to: {user.score}")
        
        return jsonify({
            'success': True,
            'message': f'Correct! +{challenge.points} points (+{bonus_points} bonus)',
            'points': total_points,
            'bonus': bonus_points
        })
    else:
        db.session.commit()
        logger.info(f"Incorrect flag rejected for user {user.username}")
        return jsonify({'success': False, 'message': 'Incorrect flag'})

@app.route('/scoreboard')
@login_required
@not_banned
def scoreboard():
    logger.info("Loading scoreboard")
    try:
        user = db.session.get(User, session['user_id'])
        if not user:
            logger.error(f"User not found in session: {session.get('user_id')}")
            return redirect(url_for('logout'))
        
        users = User.query.filter_by(is_banned=False).order_by(User.score.desc()).all()
        
        scoreboard_data = []
        for rank, u in enumerate(users, 1):
            solve_count = Solve.query.filter_by(user_id=u.id).count()
            scoreboard_data.append({
                'rank': rank,
                'user': u,
                'solve_count': solve_count
            })
        
        logger.info(f"Scoreboard loaded with {len(scoreboard_data)} entries")
        return render_template('scoreboard.html', user=user, scoreboard=scoreboard_data)
    except Exception as e:
        logger.error(f"Error loading scoreboard: {str(e)}", exc_info=True)
        return render_template('scoreboard.html', user=user, scoreboard=[])

@app.route('/api/scoreboard')
@login_required
def api_scoreboard():
    logger.info("API: Fetching scoreboard data")
    try:
        users = User.query.filter_by(is_banned=False).order_by(User.score.desc()).limit(50).all()
        data = []
        for rank, u in enumerate(users, 1):
            solve_count = Solve.query.filter_by(user_id=u.id).count()
            data.append({
                'rank': rank,
                'username': u.username,
                'score': u.score,
                'solve_count': solve_count
            })
        logger.info(f"API: Returning {len(data)} scoreboard entries")
        return jsonify(data)
    except Exception as e:
        logger.error(f"API Error fetching scoreboard: {str(e)}", exc_info=True)
        return jsonify([])

@app.route('/profile')
@login_required
@not_banned
def profile():
    logger.info("Loading profile")
    try:
        user = db.session.get(User, session['user_id'])
        if not user:
            logger.error(f"User not found in session: {session.get('user_id')}")
            return redirect(url_for('logout'))
        
        solves = Solve.query.filter_by(user_id=user.id).order_by(Solve.solved_at.desc()).all()
        submissions = Submission.query.filter_by(user_id=user.id).order_by(Submission.submitted_at.desc()).limit(20).all()
        
        logger.info(f"Profile loaded for user {user.username}")
        return render_template('profile.html', user=user, solves=solves, submissions=submissions)
    except Exception as e:
        logger.error(f"Error loading profile: {str(e)}", exc_info=True)
        return render_template('profile.html', user=user, solves=[], submissions=[])

@app.route('/admin')
@login_required
@admin_required
def admin():
    user = db.session.get(User, session['user_id'])
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin.html', user=user, users=users)

# Admin API Routes
@app.route('/admin/users/<int:user_id>/ban', methods=['POST'])
@login_required
@admin_required
def ban_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    if user.username == 'GuildMaster':
        return jsonify({'success': False, 'message': 'Cannot ban the main admin'})
    user.is_banned = not user.is_banned
    db.session.commit()
    return jsonify({'success': True, 'banned': user.is_banned})

@app.route('/admin/users/<int:user_id>/reset-score', methods=['POST'])
@login_required
@admin_required
def reset_user_score(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    user.score = 0
    db.session.commit()
    return jsonify({'success': True, 'message': 'Score reset successfully'})

# IDOR Challenge Routes
@app.route('/api/tickets')
@login_required
def api_tickets():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id parameter required'}), 400
    
    # VULNERABLE: No authorization check on user_id
    tickets = Ticket.query.filter_by(user_id=user_id).all()
    
    result = []
    for ticket in tickets:
        result.append({
            'id': ticket.id,
            'title': ticket.title,
            'description': ticket.description,
            'status': ticket.status,
            'priority': ticket.priority,
            'created_at': ticket.created_at.isoformat() if ticket.created_at else None
        })
    
    return jsonify(result)

@app.route('/api/payroll/view')
@login_required
def api_payroll_view():
    emp_id = request.args.get('id')
    if not emp_id:
        return jsonify({'error': 'id parameter required'}), 400
    
    # VULNERABLE: No authorization check on employee ID
    record = PayrollRecord.query.filter_by(employee_id=emp_id).first()
    
    if not record:
        return jsonify({'error': 'Employee not found'}), 404
    
    return jsonify({
        'employee_id': record.employee_id,
        'name': record.name,
        'department': record.department,
        'position': record.position,
        'salary': record.salary,
        'notes': record.notes
    })

@app.route('/api/files/view')
@login_required
def api_files_view():
    file_id = request.args.get('file_id', type=int)
    if not file_id:
        return jsonify({'error': 'file_id parameter required'}), 400
    
    # VULNERABLE: No ownership validation
    file = CloudFile.query.filter_by(file_id=file_id).first()
    
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    return jsonify({
        'file_id': file.file_id,
        'filename': file.filename,
        'content': file.content,
        'owner_id': file.owner_id,
        'created_at': file.created_at.isoformat() if file.created_at else None
    })

@app.route('/api/user/<int:profile_id>')
@login_required
def api_user_profile(profile_id):
    # VULNERABLE: No authorization check on profile_id
    profile = ApiProfile.query.filter_by(profile_id=profile_id).first()
    
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    return jsonify({
        'profile_id': profile.profile_id,
        'username': profile.username,
        'email': profile.email,
        'role': profile.role,
        'metadata': profile.meta_data
    })

@app.route('/api/orders/<int:order_id>')
@login_required
def api_orders(order_id):
    # VULNERABLE: No authorization check on order_id
    order = Order.query.filter_by(order_id=order_id).first()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify({
        'order_id': order.order_id,
        'customer_id': order.customer_id,
        'customer_name': order.customer_name,
        'items': order.items,
        'total_amount': order.total_amount,
        'status': order.status,
        'notes': order.notes
    })

# Cookie-Based Challenge Routes
@app.route('/challenge/cookie-role')
@login_required
def cookie_role_challenge():
    role = request.cookies.get('role', 'user')
    
    if role == 'admin':
        flag = 'flag{cookie_role_escalation_success}'
        return jsonify({'message': 'Admin access granted', 'flag': flag})
    
    return jsonify({'message': 'Access denied. User role only.'})

@app.route('/challenge/cookie-base64')
@login_required
def cookie_base64_challenge():
    import base64
    
    session_cookie = request.cookies.get('session')
    if not session_cookie:
        return jsonify({'message': 'No session cookie found'})
    
    try:
        decoded = base64.b64decode(session_cookie).decode('utf-8')
        session_data = eval(decoded)  # VULNERABLE: Unsafe eval
        
        if session_data.get('role') == 'admin':
            flag = 'flag{base64_cookie_manipulation_success}'
            return jsonify({'message': 'Admin access granted', 'flag': flag})
        
        return jsonify({'message': 'Access denied. User role only.'})
    except:
        return jsonify({'message': 'Invalid session cookie'})

@app.route('/challenge/cookie-integrity')
@login_required
def cookie_integrity_challenge():
    user_cookie = request.cookies.get('user')
    auth_cookie = request.cookies.get('auth', 'false')
    
    # VULNERABLE: Flawed logic - checks user=admin but doesn't validate auth properly
    if user_cookie == 'admin' and auth_cookie == 'false':
        flag = 'flag{cookie_integrity_flaw_success}'
        return jsonify({'message': 'Admin access granted', 'flag': flag})
    
    return jsonify({'message': 'Access denied'})

@app.route('/challenge/cookie-jwt')
@login_required
def cookie_jwt_challenge():
    import json
    import base64
    
    jwt_cookie = request.cookies.get('jwt')
    if not jwt_cookie:
        return jsonify({'message': 'No JWT cookie found'})
    
    try:
        # VULNERABLE: No signature verification
        parts = jwt_cookie.split('.')
        payload = base64.urlsafe_b64decode(parts[1] + '=' * (-len(parts[1]) % 4)).decode('utf-8')
        payload_data = json.loads(payload)
        
        if payload_data.get('role') == 'admin':
            flag = 'flag{jwt_misconfiguration_success}'
            return jsonify({'message': 'Admin access granted', 'flag': flag})
        
        return jsonify({'message': 'Access denied. User role only.'})
    except:
        return jsonify({'message': 'Invalid JWT cookie'})

@app.route('/challenge/cookie-hidden')
@login_required
def cookie_hidden_challenge():
    theme = request.cookies.get('theme', 'light')
    
    if theme == 'admin':
        flag = 'flag{hidden_cookie_behavior_success}'
        return jsonify({'message': 'Hidden panel activated', 'flag': flag})
    
    return jsonify({'message': f'Theme set to: {theme}'})

# Hybrid Challenge Routes
@app.route('/challenge/hybrid/admin-panel')
@login_required
def hybrid_admin_panel():
    # First check IDOR vulnerability
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id parameter required'}), 400
    
    # VULNERABLE: No authorization check on user_id
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Then check cookie
    admin_cookie = request.cookies.get('admin_access')
    if admin_cookie != 'granted':
        return jsonify({'message': 'Admin cookie required'})
    
    # Both vulnerabilities exploited
    if user.is_admin:
        flag = 'flag{hybrid_admin_breach_success}'
        return jsonify({'message': 'Full admin access granted', 'flag': flag})
    
    return jsonify({'message': 'User found but not admin'})

# Advanced IDOR Challenge Routes
@app.route('/api/projects')
@login_required
def api_projects():
    team_id = request.args.get('team_id', type=int)
    if not team_id:
        return jsonify({'error': 'team_id parameter required'}), 400
    
    # VULNERABLE: No authorization check on team_id
    projects = Project.query.filter_by(team_id=team_id).all()
    
    result = []
    for project in projects:
        result.append({
            'project_id': project.project_id,
            'name': project.name,
            'description': project.description,
            'status': project.status,
            'documents': project.documents
        })
    
    return jsonify(result)

@app.route('/records/view')
@login_required
def api_medical_records():
    record_id = request.args.get('record_id', type=int)
    if not record_id:
        return jsonify({'error': 'record_id parameter required'}), 400
    
    # VULNERABLE: No ownership validation
    record = MedicalRecord.query.filter_by(record_id=record_id).first()
    
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    
    return jsonify({
        'record_id': record.record_id,
        'patient_name': record.patient_name,
        'diagnosis': record.diagnosis,
        'treatment': record.treatment,
        'doctor_notes': record.doctor_notes,
        'admission_date': record.admission_date.isoformat() if record.admission_date else None
    })

@app.route('/api/invoices/<invoice_number>')
@login_required
def api_invoices(invoice_number):
    # VULNERABLE: No authorization check on invoice number
    invoice = Invoice.query.filter_by(invoice_number=invoice_number).first()
    
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404
    
    return jsonify({
        'invoice_number': invoice.invoice_number,
        'client_name': invoice.client_name,
        'amount': invoice.amount,
        'status': invoice.status,
        'items': invoice.items,
        'metadata': invoice.invoice_metadata
    })

@app.route('/messages/thread/<int:thread_id>')
@login_required
def api_messages(thread_id):
    # VULNERABLE: No ownership validation
    thread = MessageThread.query.filter_by(thread_id=thread_id).first()
    
    if not thread:
        return jsonify({'error': 'Thread not found'}), 404
    
    return jsonify({
        'thread_id': thread.thread_id,
        'subject': thread.subject,
        'participants': thread.participants,
        'messages': thread.messages,
        'created_at': thread.created_at.isoformat() if thread.created_at else None
    })

@app.route('/api/tasks')
@login_required
def api_tasks():
    project = request.args.get('project')
    if not project:
        return jsonify({'error': 'project parameter required'}), 400
    
    # VULNERABLE: No authorization check on project
    tasks = Task.query.filter_by(project=project).all()
    
    result = []
    for task in tasks:
        result.append({
            'task_id': task.task_id,
            'title': task.title,
            'description': task.description,
            'project': task.project,
            'priority': task.priority,
            'status': task.status,
            'assignee': task.assignee
        })
    
    return jsonify(result)

# Advanced Cookie Challenge Routes
@app.route('/challenge/cookie-multi-field')
@login_required
def cookie_multi_field():
    user_id = request.cookies.get('user_id')
    role = request.cookies.get('role', 'user')
    access_level = request.cookies.get('access_level', '1')
    
    # VULNERABLE: All fields must align, but no server-side validation
    if user_id and role == 'admin' and access_level == '5':
        flag = 'flag{multi_field_cookie_success}'
        return jsonify({'message': 'Admin access granted', 'flag': flag})
    
    return jsonify({'message': 'Access denied. Insufficient privileges.'})

@app.route('/challenge/cookie-signed')
@login_required
def cookie_signed():
    data = request.cookies.get('data')
    sig = request.cookies.get('sig')
    
    if not data or not sig:
        return jsonify({'message': 'Missing cookies'})
    
    # VULNERABLE: Weak signature validation (only checks if sig exists and is numeric)
    try:
        sig_int = int(sig)
        if sig_int > 0 and data:
            import base64
            decoded = base64.b64decode(data).decode('utf-8')
            session_data = eval(decoded)
            
            if session_data.get('role') == 'admin':
                flag = 'flag{weak_signature_bypass_success}'
                return jsonify({'message': 'Admin access granted', 'flag': flag})
    except:
        pass
    
    return jsonify({'message': 'Access denied'})

@app.route('/challenge/cookie-time-based')
@login_required
def cookie_time_based():
    session_cookie = request.cookies.get('session')
    if not session_cookie:
        return jsonify({'message': 'No session cookie found'})
    
    try:
        import base64
        decoded = base64.b64decode(session_cookie).decode('utf-8')
        session_data = eval(decoded)
        
        # VULNERABLE: Time-based access control (manipulatable)
        role = session_data.get('role', 'user')
        time_val = session_data.get('time', 0)
        
        if role == 'admin' and time_val > 1000000:
            flag = 'flag{time_based_cookie_success}'
            return jsonify({'message': 'Admin access granted', 'flag': flag})
    except:
        pass
    
    return jsonify({'message': 'Access denied'})

@app.route('/challenge/cookie-nested')
@login_required
def cookie_nested():
    nested_cookie = request.cookies.get('nested')
    if not nested_cookie:
        return jsonify({'message': 'No nested cookie found'})
    
    try:
        import base64
        # First decode
        first_decode = base64.b64decode(nested_cookie).decode('utf-8')
        # Parse as JSON
        import json
        json_data = json.loads(first_decode)
        # Second decode
        second_decode = base64.b64decode(json_data['inner']).decode('utf-8')
        session_data = json.loads(second_decode)
        
        if session_data.get('role') == 'admin':
            flag = 'flag{nested_encoding_success}'
            return jsonify({'message': 'Admin access granted', 'flag': flag})
    except:
        pass
    
    return jsonify({'message': 'Access denied'})

@app.route('/challenge/cookie-feature-flag')
@login_required
def cookie_feature_flag():
    features = request.cookies.get('features', 'basic')
    
    # VULNERABLE: Feature flag allows hidden features
    if 'admin_panel' in features or 'debug_mode' in features:
        flag = 'flag{feature_flag_success}'
        return jsonify({'message': 'Hidden feature enabled', 'flag': flag})
    
    return jsonify({'message': f'Current features: {features}'})

# Advanced Hybrid Challenge Routes
@app.route('/challenge/hybrid/api-gateway')
@login_required
def hybrid_api_gateway():
    # IDOR vulnerability - access data by ID
    data_id = request.args.get('id', type=int)
    if not data_id:
        return jsonify({'error': 'id parameter required'}), 400
    
    # VULNERABLE: No authorization check on data_id
    # Simulate data lookup
    data_map = {
        120: {'type': 'user', 'name': 'Standard User', 'access': 'limited'},
        121: {'type': 'user', 'name': 'Regular User', 'access': 'limited'},
        999: {'type': 'admin', 'name': 'System Administrator', 'access': 'full', 'hint': 'flag{hybrid_api_gateway_success}'}
    }
    
    data = data_map.get(data_id, {'error': 'Data not found'})
    
    if data.get('type') == 'admin':
        # Cookie vulnerability - require session cookie
        session_cookie = request.cookies.get('gateway_session')
        if session_cookie == 'admin_authorized':
            flag = data.get('hint')
            return jsonify({'message': 'Full admin access granted', 'flag': flag})
        else:
            return jsonify({'message': 'Admin data found but session required', 'data': data})
    
    return jsonify({'data': data})

# Initialize database
with app.app_context():
    db.create_all()
    initialize_challenges()
    initialize_idor_challenge_data()
    initialize_advanced_challenge_data()
    create_default_admin()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
