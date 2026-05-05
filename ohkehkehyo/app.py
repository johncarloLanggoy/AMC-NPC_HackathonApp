import os
import csv
import io
import re
import json
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler

from config import Config
from models import db, User, Teacher, Evaluation, AuditLog, Program, EmailReminder
from models import Section, ClassAssignment, Enrollment, ClassEvaluation
from utils import (generate_pdf_report, generate_csv_report, generate_audit_log_csv, 
                  send_reminder_email, calculate_teacher_stats, check_evaluation_eligibility)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
mail = Mail(app)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Role-based access control decorator
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Audit logging function
def log_action(action, details=None):
    if current_user.is_authenticated:
        log = AuditLog(
            user_id=current_user.id,
            action=action,
            details=details or request.path,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_redirect'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=request.form.get('remember', False))
            
            log_action('LOGIN', f'User logged in successfully')
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard_redirect'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/dashboard-redirect')
@login_required
def dashboard_redirect():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'program_head':
        return redirect(url_for('program_head_dashboard'))
    elif current_user.role == 'dean':
        return redirect(url_for('dean_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))

@app.route('/logout')
@login_required
def logout():
    log_action('LOGOUT', 'User logged out')
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/student/dashboard')
@login_required
@role_required('student')
def student_dashboard():
    # Get teachers available for evaluation (old system)
    teachers = Teacher.query.filter_by(is_active=True).all()
    
    # Check which teachers already evaluated
    evaluated = Evaluation.query.filter_by(
        evaluator_id=current_user.id,
        evaluator_role='student'
    ).with_entities(Evaluation.teacher_id).all()
    evaluated_ids = [e[0] for e in evaluated]
    
    # Get recent evaluations by this student (old system)
    recent_evaluations = Evaluation.query.filter_by(
        evaluator_id=current_user.id,
        evaluator_role='student'
    ).order_by(Evaluation.submitted_at.desc()).limit(5).all()
    
    # Calculate average rating
    total_score = 0
    for eval in recent_evaluations:
        total_score += eval.calculate_raw_score()
    avg_rating = total_score / len(recent_evaluations) if recent_evaluations else 0
    
    # Get all sections for potential enrollment
    sections = Section.query.filter_by(is_active=True).all()
    
    # IMPORTANT: Pass Section model to template for the irregular student section
    return render_template('student/dashboard.html', 
                         teachers=teachers, 
                         evaluated_ids=evaluated_ids,
                         recent_evaluations=recent_evaluations,
                         avg_rating=avg_rating,
                         sections=sections,
                         Section=Section)  # <-- ADD THIS LINE

@app.route('/student/evaluate/<int:teacher_id>', methods=['GET', 'POST'])
@login_required
@role_required('student')
def student_evaluate(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    
    eligible, message = check_evaluation_eligibility(current_user, teacher_id)
    if not eligible:
        flash(message, 'warning')
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        try:
            evaluation = Evaluation(
                teacher_id=teacher_id,
                evaluator_id=current_user.id,
                evaluator_role='student',
                teaching_clarity=int(request.form['teaching_clarity']),
                engagement=int(request.form['engagement']),
                fairness=int(request.form['fairness']),
                comments=request.form.get('comments', ''),
                is_anonymous=request.form.get('anonymous') == 'on'
            )
            
            db.session.add(evaluation)
            db.session.commit()
            
            log_action('SUBMIT_EVALUATION', f'Submitted student evaluation for teacher {teacher_id}')
            
            flash('Evaluation submitted successfully! Thank you for your feedback.', 'success')
            return redirect(url_for('student_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your evaluation. Please try again.', 'danger')
            app.logger.error(f"Evaluation submission error: {str(e)}")
    
    return render_template('student/evaluation.html', teacher=teacher)

# Enrollment Route
@app.route('/enroll/section/<int:section_id>')
@login_required
@role_required('student')
def enroll_section(section_id):
    """Allow student to enroll in a section"""
    section = Section.query.get_or_404(section_id)
    
    existing = Enrollment.query.filter_by(
        student_id=current_user.id,
        section_id=section_id,
        is_active=True
    ).first()
    
    if existing:
        flash(f'You are already enrolled in {section.name}', 'warning')
    else:
        enrollment = Enrollment(
            student_id=current_user.id,
            section_id=section_id,
            is_active=True
        )
        db.session.add(enrollment)
        db.session.commit()
        flash(f'Successfully enrolled in {section.name}!', 'success')
    
    return redirect(url_for('student_dashboard'))

# Program Head Routes
@app.route('/program-head/dashboard')
@login_required
@role_required('program_head')
def program_head_dashboard():
    # Get teachers only from the program head's department
    teachers = Teacher.query.filter(
        Teacher.department == current_user.department,
        Teacher.is_active == True
    ).all()
    
    # Get evaluated teachers (by this program head)
    evaluated_teachers = db.session.query(Evaluation.teacher_id).filter(
        Evaluation.evaluator_id == current_user.id,
        Evaluation.evaluator_role == 'program_head'
    ).distinct().all()
    evaluated_ids = [e[0] for e in evaluated_teachers]
    
    teacher_stats = []
    for teacher in teachers:
        # Get ALL evaluations for this teacher (from all roles)
        all_evaluations = Evaluation.query.filter_by(teacher_id=teacher.id).all()
        
        # Calculate average score from all evaluations
        if all_evaluations:
            total_raw = sum(e.calculate_raw_score() for e in all_evaluations)
            avg_score = total_raw / len(all_evaluations)
        else:
            avg_score = 0
        
        # Check if program head has already evaluated this teacher
        is_evaluated_by_ph = teacher.id in evaluated_ids
        
        teacher_stats.append({
            'teacher': teacher,
            'avg_score': round(avg_score, 2),
            'eval_count': len(all_evaluations),
            'evaluated': is_evaluated_by_ph  # This controls the status badge
        })
    
    # Calculate department statistics
    total_teachers = len(teachers)
    evaluated_count = len([t for t in teacher_stats if t['evaluated']])
    pending_count = total_teachers - evaluated_count
    
    # Calculate department average score (only from teachers with evaluations)
    teachers_with_evals = [t for t in teacher_stats if t['eval_count'] > 0]
    if teachers_with_evals:
        dept_avg = sum(t['avg_score'] for t in teachers_with_evals) / len(teachers_with_evals)
    else:
        dept_avg = 0
    
    return render_template('program_head/dashboard.html', 
                         teachers=teachers,
                         teacher_stats=teacher_stats,
                         evaluated_ids=evaluated_ids,
                         total_teachers=total_teachers,
                         evaluated_count=evaluated_count,
                         pending_count=pending_count,
                         dept_avg=round(dept_avg, 2))

@app.route('/program-head/evaluate/<int:teacher_id>', methods=['GET', 'POST'])
@login_required
@role_required('program_head')
def program_head_evaluate(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    
    # Check if teacher is in the program head's department
    if teacher.department != current_user.department:
        flash(f'You can only evaluate teachers in your department ({current_user.department}).', 'danger')
        return redirect(url_for('program_head_dashboard'))
    
    existing = Evaluation.query.filter_by(
        teacher_id=teacher_id,
        evaluator_id=current_user.id,
        evaluator_role='program_head'
    ).first()
    
    if existing:
        flash('You have already evaluated this teacher', 'warning')
        return redirect(url_for('program_head_dashboard'))
    
    if request.method == 'POST':
        try:
            evaluation = Evaluation(
                teacher_id=teacher_id,
                evaluator_id=current_user.id,
                evaluator_role='program_head',
                curriculum_implementation=int(request.form['curriculum']),
                assessment_quality=int(request.form['assessment']),
                mentoring=int(request.form['mentoring']),
                comments=request.form.get('comments', '')
            )
            
            db.session.add(evaluation)
            db.session.commit()
            
            log_action('SUBMIT_EVALUATION', f'Program head ({current_user.department}) submitted evaluation for teacher {teacher_id}')
            
            flash('Evaluation submitted successfully!', 'success')
            return redirect(url_for('program_head_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your evaluation.', 'danger')
            app.logger.error(f"Program head evaluation error: {str(e)}")
    
    return render_template('program_head/evaluation.html', teacher=teacher)

# Dean Routes
@app.route('/dean/dashboard')
@login_required
@role_required('dean')
def dean_dashboard():
    teachers = Teacher.query.filter_by(is_active=True).all()
    
    total_teachers = len(teachers)
    total_evaluations = Evaluation.query.count()
    
    all_evaluations = Evaluation.query.all()
    if all_evaluations:
        total_score = sum(e.calculate_weighted_score() for e in all_evaluations)
        avg_score_all = total_score / len(all_evaluations)
    else:
        avg_score_all = 0
    
    evaluated_ids = db.session.query(Evaluation.teacher_id).filter_by(
        evaluator_role='dean'
    ).distinct().all()
    evaluated_ids = [e[0] for e in evaluated_ids]
    pending_teachers = [t for t in teachers if t.id not in evaluated_ids]
    
    return render_template('dean/dashboard.html',
                         teachers=teachers,
                         total_teachers=total_teachers,
                         total_evaluations=total_evaluations,
                         avg_score_all=round(avg_score_all, 2),
                         pending_teachers=pending_teachers)

@app.route('/dean/evaluate/<int:teacher_id>', methods=['GET', 'POST'])
@login_required
@role_required('dean')
def dean_evaluate(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    
    existing = Evaluation.query.filter_by(
        teacher_id=teacher_id,
        evaluator_id=current_user.id,
        evaluator_role='dean'
    ).first()
    
    if existing:
        flash('You have already evaluated this teacher', 'warning')
        return redirect(url_for('dean_dashboard'))
    
    if request.method == 'POST':
        try:
            evaluation = Evaluation(
                teacher_id=teacher_id,
                evaluator_id=current_user.id,
                evaluator_role='dean',
                attendance=int(request.form['attendance']),
                commitment=int(request.form['commitment']),
                teaching_quality=int(request.form['teaching_quality']),
                comments=request.form.get('comments', '')
            )
            
            db.session.add(evaluation)
            db.session.commit()
            
            log_action('SUBMIT_EVALUATION', f'Submitted dean evaluation for teacher {teacher_id}')
            
            flash('Evaluation submitted successfully!', 'success')
            return redirect(url_for('dean_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your evaluation.', 'danger')
            app.logger.error(f"Dean evaluation error: {str(e)}")
    
    return render_template('dean/evaluation.html', teacher=teacher)

# Admin Routes
@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    from models import ClassEvaluation, ClassAssignment, Section, Enrollment
    
    total_teachers = Teacher.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_program_heads = User.query.filter_by(role='program_head').count()
    total_deans = User.query.filter_by(role='dean').count()
    
    old_evaluations = Evaluation.query.count()
    new_evaluations = ClassEvaluation.query.count()
    total_evaluations = old_evaluations + new_evaluations
    
    total_class_evaluations = new_evaluations
    total_sections = Section.query.filter_by(is_active=True).count()
    total_class_assignments = ClassAssignment.query.filter_by(is_active=True).count()
    
    teachers_count = Teacher.query.count()
    students_count = User.query.filter_by(role='student').count()
    program_heads_count = User.query.filter_by(role='program_head').count()
    deans_count = User.query.filter_by(role='dean').count()
    
    old_possible = teachers_count * (students_count + program_heads_count + deans_count)
    old_pending = old_possible - old_evaluations if old_possible > old_evaluations else 0
    
    total_possible_class_evals = 0
    sections = Section.query.filter_by(is_active=True).all()
    for section in sections:
        students_in_section = Enrollment.query.filter_by(section_id=section.id, is_active=True).count()
        classes_in_section = ClassAssignment.query.filter_by(section_id=section.id, is_active=True).count()
        total_possible_class_evals += students_in_section * classes_in_section
    
    new_pending = total_possible_class_evals - new_evaluations if total_possible_class_evals > new_evaluations else 0
    pending_evaluations = old_pending + new_pending
    
    old_recent = Evaluation.query.order_by(Evaluation.submitted_at.desc()).limit(10).all()
    new_recent = ClassEvaluation.query.order_by(ClassEvaluation.submitted_at.desc()).limit(10).all()
    
    recent_list = []
    for eval in old_recent:
        recent_list.append({
            'type': 'teacher',
            'submitted_at': eval.submitted_at,
            'teacher_name': eval.teacher.name,
            'department': eval.teacher.department,
            'evaluator_role': eval.evaluator_role,
            'score': eval.calculate_weighted_score(),
            'teacher_id': eval.teacher_id,
            'subject_name': None,
            'section_name': None
        })
    
    for eval in new_recent:
        recent_list.append({
            'type': 'class',
            'submitted_at': eval.submitted_at,
            'teacher_name': eval.class_assignment.teacher.name,
            'department': eval.class_assignment.teacher.department,
            'subject_name': eval.class_assignment.subject_name,
            'section_name': eval.class_assignment.section.name,
            'evaluator_role': 'student',
            'score': eval.calculate_raw_score(),
            'teacher_id': eval.class_assignment.teacher_id
        })
    
    recent_list.sort(key=lambda x: x['submitted_at'], reverse=True)
    recent_evaluations = recent_list[:10]
    
    student_evals = Evaluation.query.filter_by(evaluator_role='student').count()
    program_head_evals = Evaluation.query.filter_by(evaluator_role='program_head').count()
    dean_evals = Evaluation.query.filter_by(evaluator_role='dean').count()
    class_evals = new_evaluations
    
    # Get irregular student count
    irregular_students = User.query.filter_by(role='student', is_irregular=True).count()
    regular_students = total_students - irregular_students
    
    return render_template('admin/dashboard.html',
                         total_teachers=total_teachers,
                         total_students=total_students,
                         total_program_heads=total_program_heads,
                         total_deans=total_deans,
                         total_evaluations=total_evaluations,
                         total_class_evaluations=total_class_evaluations,
                         total_sections=total_sections,
                         total_class_assignments=total_class_assignments,
                         pending_evaluations=pending_evaluations,
                         recent_evaluations=recent_evaluations,
                         student_evals=student_evals,
                         program_head_evals=program_head_evals,
                         dean_evals=dean_evals,
                         class_evals=class_evals,
                         regular_students=regular_students,
                         irregular_students=irregular_students)

@app.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    teachers = Teacher.query.order_by(Teacher.name).all()
    programs = Program.query.all()
    return render_template('admin/users.html', users=users, teachers=teachers, programs=programs)

@app.route('/admin/add-user', methods=['POST'])
@login_required
@role_required('admin')
def add_user():
    try:
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            full_name=request.form['full_name'],
            role=request.form['role'],
            department=request.form.get('department'),
            roll_number=request.form.get('roll_number'),
            program=request.form.get('program'),
            semester=request.form.get('semester', type=int) if request.form.get('semester') else None,
            is_irregular=request.form.get('is_irregular') == 'on'
        )
        user.set_password(request.form['password'])
        
        db.session.add(user)
        db.session.commit()
        
        log_action('ADD_USER', f'Added new user: {user.username} ({user.role})')
        flash(f'User {user.full_name} added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding user: {str(e)}', 'danger')
        app.logger.error(f"Add user error: {str(e)}")
    
    return redirect(url_for('admin_users'))

@app.route('/admin/edit-user', methods=['POST'])
@login_required
@role_required('admin')
def edit_user():
    try:
        user_id = request.form.get('user_id')
        user = User.query.get_or_404(user_id)
        
        user.username = request.form['username']
        user.full_name = request.form['full_name']
        user.email = request.form['email']
        user.role = request.form['role']
        user.department = request.form.get('department')
        user.is_irregular = request.form.get('is_irregular') == 'on'
        
        if request.form.get('password'):
            user.set_password(request.form['password'])
        
        db.session.commit()
        
        log_action('EDIT_USER', f'Edited user: {user.username}')
        flash(f'User {user.full_name} updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user: {str(e)}', 'danger')
        app.logger.error(f"Edit user error: {str(e)}")
    
    return redirect(url_for('admin_users'))

@app.route('/admin/edit-teacher', methods=['POST'])
@login_required
@role_required('admin')
def edit_teacher():
    try:
        teacher_id = request.form.get('teacher_id')
        teacher = Teacher.query.get_or_404(teacher_id)
        
        teacher.name = request.form['name']
        teacher.email = request.form['email']
        teacher.department = request.form['department']
        teacher.subjects = request.form['subjects']
        
        db.session.commit()
        
        log_action('EDIT_TEACHER', f'Edited teacher: {teacher.name}')
        flash(f'Teacher {teacher.name} updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating teacher: {str(e)}', 'danger')
        app.logger.error(f"Edit teacher error: {str(e)}")
    
    return redirect(url_for('admin_users'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        if user.id == current_user.id:
            flash('You cannot delete your own account!', 'danger')
            return redirect(url_for('admin_users'))
        
        username = user.username
        full_name = user.full_name
        
        db.session.delete(user)
        db.session.commit()
        
        log_action('DELETE_USER', f'Deleted user: {username}')
        flash(f'User {full_name} deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
        app.logger.error(f"Delete user error: {str(e)}")
    
    return redirect(url_for('admin_users'))

@app.route('/admin/delete-teacher/<int:teacher_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_teacher(teacher_id):
    try:
        teacher = Teacher.query.get_or_404(teacher_id)
        teacher_name = teacher.name
        
        db.session.delete(teacher)
        db.session.commit()
        
        log_action('DELETE_TEACHER', f'Deleted teacher: {teacher_name}')
        flash(f'Teacher {teacher_name} deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting teacher: {str(e)}', 'danger')
        app.logger.error(f"Delete teacher error: {str(e)}")
    
    return redirect(url_for('admin_users'))

@app.route('/admin/add-teacher', methods=['POST'])
@login_required
@role_required('admin')
def add_teacher():
    try:
        teacher = Teacher(
            name=request.form['name'],
            email=request.form['email'],
            department=request.form['department'],
            subjects=request.form['subjects']
        )
        
        db.session.add(teacher)
        db.session.commit()
        
        log_action('ADD_TEACHER', f'Added new teacher: {teacher.name}')
        flash(f'Teacher {teacher.name} added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding teacher: {str(e)}', 'danger')
        app.logger.error(f"Add teacher error: {str(e)}")
    
    return redirect(url_for('admin_users'))

@app.route('/admin/add-program', methods=['POST'])
@login_required
@role_required('admin')
def add_program():
    try:
        program = Program(
            name=request.form['name'],
            department=request.form['department'],
            coordinator_id=request.form.get('coordinator_id')
        )
        
        db.session.add(program)
        db.session.commit()
        
        log_action('ADD_PROGRAM', f'Added new program: {program.name}')
        flash(f'Program {program.name} added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding program: {str(e)}', 'danger')
        app.logger.error(f"Add program error: {str(e)}")
    
    return redirect(url_for('admin_users'))

@app.route('/admin/audit-logs')
@login_required
@role_required('admin')
def audit_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    logs = AuditLog.query.order_by(
        AuditLog.timestamp.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/audit_logs.html', logs=logs)

@app.route('/admin/export-audit-logs')
@login_required
@role_required('admin')
def export_audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(1000).all()
    csv_data = generate_audit_log_csv(logs)
    
    response = make_response(csv_data.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    log_action('EXPORT_AUDIT_LOGS', 'Exported audit logs to CSV')
    return response

@app.route('/admin/email-reminders', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def email_reminders():
    from datetime import datetime
    
    if request.method == 'POST':
        role = request.form['role']
        deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d')
        
        users = User.query.filter_by(role=role, is_active=True).all()
        
        for user in users:
            reminder = EmailReminder(
                recipient_email=user.email,
                recipient_role=role,
                subject='Teacher Evaluation Reminder',
                message=f'Please complete your pending evaluations by {deadline.strftime("%Y-%m-%d")}',
                scheduled_for=deadline
            )
            db.session.add(reminder)
            
            run_date = deadline - timedelta(days=1)
            scheduler.add_job(
                func=send_reminder_email,
                trigger='date',
                run_date=run_date,
                args=[user.email, user.full_name, deadline, app],
                id=f"reminder_{user.id}_{deadline.timestamp()}"
            )
        
        db.session.commit()
        flash(f'Reminders scheduled for {len(users)} users', 'success')
        
    reminders = EmailReminder.query.order_by(EmailReminder.scheduled_for.desc()).limit(50).all()
    now = datetime.now()
    
    return render_template('admin/email_reminders.html', reminders=reminders, now=now)

@app.route('/api/cancel-reminder/<int:reminder_id>', methods=['POST'])
@login_required
@role_required('admin')
def cancel_reminder(reminder_id):
    reminder = EmailReminder.query.get_or_404(reminder_id)
    
    try:
        job_id = f"reminder_{reminder.id}_{reminder.scheduled_for.timestamp()}"
        scheduler.remove_job(job_id)
        
        reminder.status = 'cancelled'
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Shared Routes
@app.route('/teacher/<int:teacher_id>/dashboard')
@login_required
def teacher_dashboard(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    
    if current_user.role == 'student' and current_user.role != 'admin':
        if current_user.role == 'program_head' and teacher.department != current_user.department:
            abort(403)
    
    evaluations = Evaluation.query.filter_by(teacher_id=teacher_id).order_by(
        Evaluation.submitted_at.desc()
    ).all()
    
    if evaluations:
        stats = calculate_teacher_stats(teacher_id, evaluations)
    else:
        stats = {
            'total_evaluations': 0,
            'scores_by_role': {
                'student': {'avg': 0, 'count': 0},
                'program_head': {'avg': 0, 'count': 0},
                'dean': {'avg': 0, 'count': 0}
            },
            'monthly_averages': {},
            'category_averages': {
                'teaching_clarity': 0,
                'engagement': 0,
                'fairness': 0,
                'curriculum': 0,
                'assessment': 0,
                'mentoring': 0,
                'attendance': 0,
                'commitment': 0,
                'teaching_quality': 0
            }
        }
    
    evaluation_list = []
    for eval in evaluations[:20]:
        evaluation_list.append({
            'id': eval.id,
            'submitted_at': eval.submitted_at,
            'evaluator_role': eval.evaluator_role,
            'raw_score': eval.calculate_raw_score(),
            'weighted_score': eval.calculate_weighted_score(),
            'comments': eval.comments if not eval.is_anonymous or current_user.role == 'admin' else '[Anonymous]'
        })
    
    return render_template('shared/teacher_dashboard.html',
                         teacher=teacher,
                         evaluations=evaluation_list,
                         stats=stats)

@app.route('/program/<int:program_id>/dashboard')
@login_required
def program_dashboard(program_id):
    program = Program.query.get_or_404(program_id)
    teachers = program.teachers
    
    program_stats = {
        'total_teachers': len(teachers),
        'total_evaluations': 0,
        'avg_score': 0,
        'teachers_data': []
    }
    
    total_score = 0
    for teacher in teachers:
        evaluations = Evaluation.query.filter_by(teacher_id=teacher.id).all()
        if evaluations:
            teacher_avg = sum(e.calculate_weighted_score() for e in evaluations) / len(evaluations)
        else:
            teacher_avg = 0
        
        program_stats['teachers_data'].append({
            'teacher': teacher,
            'avg_score': round(teacher_avg, 2),
            'eval_count': len(evaluations)
        })
        total_score += teacher_avg
        program_stats['total_evaluations'] += len(evaluations)
    
    if teachers:
        program_stats['avg_score'] = round(total_score / len(teachers), 2)
    
    return render_template('shared/program_dashboard.html',
                         program=program,
                         program_stats=program_stats)

# Export Routes
@app.route('/export/teacher/<int:teacher_id>/pdf')
@login_required
def export_teacher_pdf(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    evaluations = Evaluation.query.filter_by(teacher_id=teacher_id).order_by(
        Evaluation.submitted_at.desc()
    ).all()
    
    teacher_data = {
        'name': teacher.name,
        'department': teacher.department,
        'total_evaluations': len(evaluations),
        'final_score': 0,
        'scores_by_role': {
            'student': {'avg': 0, 'weighted': 0, 'count': 0},
            'program_head': {'avg': 0, 'weighted': 0, 'count': 0},
            'dean': {'avg': 0, 'weighted': 0, 'count': 0}
        }
    }
    
    for role in teacher_data['scores_by_role']:
        role_evaluations = [e for e in evaluations if e.evaluator_role == role]
        if role_evaluations:
            count = len(role_evaluations)
            avg_raw = sum(e.calculate_raw_score() for e in role_evaluations) / count
            teacher_data['scores_by_role'][role] = {
                'avg': round(avg_raw, 2),
                'weighted': round(avg_raw * Config.WEIGHTS[role], 2),
                'count': count
            }
            teacher_data['final_score'] += avg_raw * Config.WEIGHTS[role]
    
    evaluation_list = []
    for eval in evaluations:
        evaluation_list.append({
            'submitted_at': eval.submitted_at,
            'evaluator_role': eval.evaluator_role,
            'raw_score': eval.calculate_raw_score(),
            'weighted_score': eval.calculate_weighted_score(),
            'comments': eval.comments
        })
    
    pdf_buffer = generate_pdf_report(teacher_data, evaluation_list)
    
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={teacher.name}_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    
    log_action('EXPORT_PDF', f'Exported PDF report for teacher {teacher_id}')
    return response

@app.route('/export/teacher/<int:teacher_id>/csv')
@login_required
def export_teacher_csv(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    evaluations = Evaluation.query.filter_by(teacher_id=teacher_id).order_by(
        Evaluation.submitted_at.desc()
    ).all()
    
    teacher_data = {
        'name': teacher.name,
        'department': teacher.department,
        'total_evaluations': len(evaluations),
        'final_score': 0,
        'scores_by_role': {
            'student': {'avg': 0, 'weighted': 0, 'count': 0},
            'program_head': {'avg': 0, 'weighted': 0, 'count': 0},
            'dean': {'avg': 0, 'weighted': 0, 'count': 0}
        }
    }
    
    for role in teacher_data['scores_by_role']:
        role_evaluations = [e for e in evaluations if e.evaluator_role == role]
        if role_evaluations:
            count = len(role_evaluations)
            avg_raw = sum(e.calculate_raw_score() for e in role_evaluations) / count
            teacher_data['scores_by_role'][role] = {
                'avg': round(avg_raw, 2),
                'weighted': round(avg_raw * Config.WEIGHTS[role], 2),
                'count': count
            }
            teacher_data['final_score'] += avg_raw * Config.WEIGHTS[role]
    
    evaluation_list = []
    for eval in evaluations:
        evaluation_list.append({
            'submitted_at': eval.submitted_at,
            'evaluator_role': eval.evaluator_role,
            'raw_score': eval.calculate_raw_score(),
            'weighted_score': eval.calculate_weighted_score(),
            'comments': eval.comments
        })
    
    csv_data = generate_csv_report(teacher_data, evaluation_list)
    
    response = make_response(csv_data.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={teacher.name}_report_{datetime.now().strftime("%Y%m%d")}.csv'
    
    log_action('EXPORT_CSV', f'Exported CSV report for teacher {teacher_id}')
    return response

# API Routes
@app.route('/api/teacher/<int:teacher_id>/stats')
@login_required
def api_teacher_stats(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    evaluations = Evaluation.query.filter_by(teacher_id=teacher_id).all()
    
    stats = calculate_teacher_stats(teacher_id, evaluations)
    stats['teacher_name'] = teacher.name
    stats['department'] = teacher.department
    
    return jsonify(stats)

@app.route('/api/teacher/<int:teacher_id>/trends')
@login_required
def api_teacher_trends(teacher_id):
    evaluations = Evaluation.query.filter_by(teacher_id=teacher_id).order_by(
        Evaluation.submitted_at
    ).all()
    
    if not evaluations:
        return jsonify({'months': [], 'scores': []})
    
    monthly_data = {}
    for eval in evaluations:
        month_key = eval.submitted_at.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {'total': 0, 'count': 0}
        monthly_data[month_key]['total'] += eval.calculate_weighted_score()
        monthly_data[month_key]['count'] += 1
    
    months = []
    scores = []
    for month in sorted(monthly_data.keys()):
        months.append(month)
        scores.append(round(monthly_data[month]['total'] / monthly_data[month]['count'], 2))
    
    return jsonify({'months': months, 'scores': scores})

@app.route('/api/user/<int:user_id>')
@login_required
@role_required('admin')
def api_get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'full_name': user.full_name,
        'email': user.email,
        'role': user.role,
        'department': user.department,
        'is_active': user.is_active,
        'is_irregular': user.is_irregular if hasattr(user, 'is_irregular') else False
    })

@app.route('/api/teacher/<int:teacher_id>')
@login_required
@role_required('admin')
def api_get_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    return jsonify({
        'id': teacher.id,
        'name': teacher.name,
        'email': teacher.email,
        'department': teacher.department,
        'subjects': teacher.subjects,
        'is_active': teacher.is_active
    })

@app.route('/api/toggle-user/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def api_toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    log_action('TOGGLE_USER', f'Toggled user {user_id} status to {user.is_active}')
    
    return jsonify({'success': True, 'is_active': user.is_active})

@app.route('/api/toggle-teacher/<int:teacher_id>', methods=['POST'])
@login_required
@role_required('admin')
def api_toggle_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    teacher.is_active = not teacher.is_active
    db.session.commit()
    
    log_action('TOGGLE_TEACHER', f'Toggled teacher {teacher_id} status to {teacher.is_active}')
    
    return jsonify({'success': True, 'is_active': teacher.is_active})

@app.route('/api/evaluations-by-role')
@login_required
@role_required('admin')
def api_evaluations_by_role():
    student_count = Evaluation.query.filter_by(evaluator_role='student').count()
    program_head_count = Evaluation.query.filter_by(evaluator_role='program_head').count()
    dean_count = Evaluation.query.filter_by(evaluator_role='dean').count()
    
    return jsonify({
        'student': student_count,
        'program_head': program_head_count,
        'dean': dean_count
    })

@app.route('/api/department-scores')
@login_required
@role_required('admin')
def api_department_scores():
    departments = db.session.query(Teacher.department).distinct().all()
    departments = [d[0] for d in departments if d[0]]
    
    scores = []
    for dept in departments:
        teachers = Teacher.query.filter_by(department=dept).all()
        teacher_ids = [t.id for t in teachers]
        
        evaluations = Evaluation.query.filter(Evaluation.teacher_id.in_(teacher_ids)).all()
        if evaluations:
            avg_score = sum(e.calculate_weighted_score() for e in evaluations) / len(evaluations)
        else:
            avg_score = 0
        
        scores.append(round(avg_score, 2))
    
    return jsonify({'departments': departments, 'scores': scores})

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Allow students to register for an account"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_redirect'))
    
    # Get all available sections for dropdown
    sections = Section.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form['username']
            student_id = request.form['student_id']
            full_name = request.form['full_name']
            section_id = request.form.get('section_id')  # Changed from year_section to section_id
            password = request.form['password']
            student_type = request.form.get('student_type', 'regular')
            is_irregular = (student_type == 'irregular')
            
            # Validate required fields
            if not all([username, student_id, full_name, section_id, password]):
                flash('All fields are required.', 'danger')
                return redirect(url_for('register'))
            
            # Get the selected section
            selected_section = Section.query.get(int(section_id))
            if not selected_section:
                flash('Invalid section selected.', 'danger')
                return redirect(url_for('register'))
            
            year_section = selected_section.name
            course = selected_section.program.split()[0] if selected_section.program else selected_section.name.split()[0]
            year = selected_section.year_level
            
            # Validate username format
            if not re.match(r'^[a-zA-Z0-9_]{5,20}$', username):
                flash('Username must be 5-20 characters and contain only letters, numbers, and underscores.', 'danger')
                return redirect(url_for('register'))
            
            # Check if username already exists
            if User.query.filter_by(username=username).first():
                flash('Username already taken. Please choose another.', 'danger')
                return redirect(url_for('register'))
            
            # Validate student ID format
            if len(student_id) < 5 or len(student_id) > 20:
                flash('Student ID must be between 5 and 20 characters.', 'danger')
                return redirect(url_for('register'))
            
            # Check if student ID already exists
            if User.query.filter_by(roll_number=student_id).first():
                flash('Student ID already registered. Please contact administration.', 'danger')
                return redirect(url_for('register'))
            
            # Validate full name format
            if not re.match(r'^[a-zA-Z\s\-\',.]+$', full_name):
                flash('Full name must be 2-100 characters and contain only letters, spaces, hyphens, apostrophes, commas, and periods.', 'danger')
                return redirect(url_for('register'))
            
            # Check if full name already exists
            if User.query.filter_by(full_name=full_name).first():
                flash('This name is already registered. Please contact administration if this is you.', 'danger')
                return redirect(url_for('register'))
            
            # Validate password strength
            if not validate_password_strength(password):
                flash('Password must be at least 8 characters and contain uppercase, lowercase, number, and special character.', 'danger')
                return redirect(url_for('register'))
            
            # Create email from student ID
            email = f"{student_id}@student.university.edu"
            
            # Check if email already exists
            if User.query.filter_by(email=email).first():
                import time
                email = f"{student_id}_{int(time.time())}@student.university.edu"
            
            # Create new student user
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                role='student',
                department=course,
                roll_number=student_id,
                program=selected_section.program,
                semester=year,
                is_active=True,
                is_irregular=is_irregular
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Auto-enroll student in the section (only for regular students)
            if not is_irregular:
                enrollment = Enrollment(
                    student_id=user.id,
                    section_id=selected_section.id,
                    is_active=True
                )
                db.session.add(enrollment)
                db.session.commit()
                flash(f'You have been automatically enrolled in {selected_section.name}.', 'info')
            
            # Log the registration
            log_action('REGISTER', f'New {"irregular" if is_irregular else "regular"} student registered: {username} - {full_name} ({selected_section.name})')
            
            flash('Registration successful! You can now login with your username.', 'success')
            return redirect(url_for('login'))
            
        except KeyError as e:
            flash(f'Missing required field: {str(e)}', 'danger')
            return redirect(url_for('register'))
        except ValueError as e:
            flash(f'Invalid data format: {str(e)}', 'danger')
            return redirect(url_for('register'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
            app.logger.error(f"Registration error: {str(e)}")
            return redirect(url_for('register'))
    
    return render_template('register.html', sections=sections)

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>\/?]', password):
        return False
    return True

@app.route('/check-username')
def check_username():
    """Check if username is available"""
    username = request.args.get('username', '').strip()
    
    if not username:
        return jsonify({'available': False, 'message': 'Username required'})
    
    if len(username) < 5:
        return jsonify({'available': False, 'message': 'Username must be at least 5 characters'})
    
    if len(username) > 20:
        return jsonify({'available': False, 'message': 'Username must be at most 20 characters'})
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return jsonify({'available': False, 'message': 'Username can only contain letters, numbers, and underscores'})
    
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'available': False, 'message': 'Username already taken'})
    
    return jsonify({'available': True, 'message': 'Username available'})

# ============================================
# SECTION-BASED EVALUATION ROUTES
# ============================================

# Idagdag ito sa app.py pagkatapos ng existing routes

@app.route('/admin/program/<int:program_id>/manage-teachers', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_program_teachers(program_id):
    """Manage teachers assigned to a specific program"""
    program = Program.query.get_or_404(program_id)
    
    # Get all teachers not already in this program
    available_teachers = Teacher.query.filter(
        Teacher.is_active == True,
        ~Teacher.programs.any(id=program_id)
    ).all()
    
    # Get teachers already in this program
    assigned_teachers = program.teachers
    
    if request.method == 'POST':
        action = request.form.get('action')
        teacher_id = request.form.get('teacher_id', type=int)
        
        if action == 'add' and teacher_id:
            teacher = Teacher.query.get_or_404(teacher_id)
            if teacher not in program.teachers:
                program.teachers.append(teacher)
                db.session.commit()
                log_action('ADD_TEACHER_TO_PROGRAM', 
                          f'Added teacher {teacher.name} to program {program.name}')
                flash(f'Teacher {teacher.name} added to {program.name}!', 'success')
        
        elif action == 'remove' and teacher_id:
            teacher = Teacher.query.get_or_404(teacher_id)
            if teacher in program.teachers:
                program.teachers.remove(teacher)
                db.session.commit()
                log_action('REMOVE_TEACHER_FROM_PROGRAM', 
                          f'Removed teacher {teacher.name} from program {program.name}')
                flash(f'Teacher {teacher.name} removed from {program.name}!', 'success')
        
        return redirect(url_for('manage_program_teachers', program_id=program_id))
    
    # Prepare teacher stats for assigned teachers
    teacher_stats = []
    for teacher in assigned_teachers:
        evaluations = Evaluation.query.filter_by(teacher_id=teacher.id).all()
        if evaluations:
            avg_score = sum(e.calculate_weighted_score() for e in evaluations) / len(evaluations)
            eval_count = len(evaluations)
        else:
            avg_score = 0
            eval_count = 0
        
        teacher_stats.append({
            'teacher': teacher,
            'avg_score': round(avg_score, 2),
            'eval_count': eval_count
        })
    
    return render_template('admin/manage_program_teachers.html',
                         program=program,
                         assigned_teachers=assigned_teachers,
                         teacher_stats=teacher_stats,
                         available_teachers=available_teachers)


@app.route('/admin/bulk-assign-teachers', methods=['POST'])
@login_required
@role_required('admin')
def bulk_assign_teachers():
    """Bulk assign teachers to a program"""
    program_id = request.form.get('program_id', type=int)
    teacher_ids = request.form.getlist('teacher_ids')
    
    program = Program.query.get_or_404(program_id)
    
    added_count = 0
    for teacher_id in teacher_ids:
        teacher = Teacher.query.get(teacher_id)
        if teacher and teacher not in program.teachers:
            program.teachers.append(teacher)
            added_count += 1
    
    db.session.commit()
    
    if added_count > 0:
        log_action('BULK_ASSIGN_TEACHERS', 
                  f'Added {added_count} teachers to program {program.name}')
        flash(f'{added_count} teacher(s) added to {program.name}!', 'success')
    else:
        flash('No new teachers were added.', 'info')
    
    return redirect(url_for('manage_program_teachers', program_id=program_id))

# Idagdag ito sa app.py

@app.route('/admin/assign-teacher-to-program', methods=['POST'])
@login_required
@role_required('admin')
def assign_teacher_to_program():
    """Assign a single teacher to a program"""
    teacher_id = request.form.get('teacher_id', type=int)
    program_id = request.form.get('program_id', type=int)
    
    teacher = Teacher.query.get_or_404(teacher_id)
    program = Program.query.get_or_404(program_id)
    
    if teacher in program.teachers:
        flash(f'{teacher.name} is already assigned to {program.name}', 'info')
    else:
        program.teachers.append(teacher)
        db.session.commit()
        log_action('ASSIGN_TEACHER_TO_PROGRAM', 
                  f'Assigned teacher {teacher.name} to program {program.name}')
        flash(f'{teacher.name} has been assigned to {program.name}!', 'success')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/program/<int:program_id>/remove-teacher', methods=['POST'])
@login_required
@role_required('admin')
def remove_teacher_from_program(program_id):
    """Remove a teacher from a program"""
    program = Program.query.get_or_404(program_id)
    teacher_id = request.form.get('teacher_id', type=int)
    teacher = Teacher.query.get_or_404(teacher_id)
    
    if teacher in program.teachers:
        program.teachers.remove(teacher)
        db.session.commit()
        log_action('REMOVE_TEACHER_FROM_PROGRAM', 
                  f'Removed teacher {teacher.name} from program {program.name}')
        flash(f'{teacher.name} has been removed from {program.name}!', 'success')
    else:
        flash(f'{teacher.name} is not in this program.', 'warning')
    
    return redirect(url_for('program_dashboard', program_id=program_id))


@app.route('/admin/assign-program-head', methods=['POST'])
@login_required
@role_required('admin')
def assign_program_head():
    """Assign a program head to a program"""
    program_id = request.form.get('program_id', type=int)
    user_id = request.form.get('user_id', type=int)
    
    program = Program.query.get_or_404(program_id)
    user = User.query.get_or_404(user_id)
    
    if user.role != 'program_head':
        flash('Selected user must have program_head role!', 'danger')
        return redirect(url_for('admin_users'))
    
    program.coordinator_id = user_id
    db.session.commit()
    
    log_action('ASSIGN_PROGRAM_HEAD', 
              f'Assigned {user.full_name} as program head for {program.name}')
    flash(f'{user.full_name} has been assigned as program head for {program.name}!', 'success')
    
    return redirect(url_for('admin_users'))

@app.route('/student/evaluate-class/<int:class_id>', methods=['GET', 'POST'])
@login_required
@role_required('student')
def student_evaluate_class(class_id):
    """Evaluate a specific class assignment"""
    class_assignment = ClassAssignment.query.get_or_404(class_id)
    
    # Check if student is enrolled in this section
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        section_id=class_assignment.section_id,
        is_active=True
    ).first()
    
    # Allow irregular students to evaluate even if not enrolled
    if not enrollment and not current_user.is_irregular:
        flash('You are not enrolled in this section. Please contact your administrator.', 'danger')
        return redirect(url_for('student_dashboard'))
    
    # For regular students, check if already evaluated
    if enrollment and not current_user.is_irregular:
        existing = ClassEvaluation.query.filter_by(
            class_assignment_id=class_id,
            evaluator_id=current_user.id
        ).first()
        
        if existing:
            flash('You have already evaluated this class.', 'warning')
            return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        try:
            evaluation = ClassEvaluation(
                class_assignment_id=class_id,
                evaluator_id=current_user.id,
                teaching_clarity=int(request.form['teaching_clarity']),
                engagement=int(request.form['engagement']),
                fairness=int(request.form['fairness']),
                subject_mastery=int(request.form['subject_mastery']),
                punctuality=int(request.form['punctuality']),
                comments=request.form.get('comments', ''),
                is_anonymous=request.form.get('anonymous') == 'on'
            )
            
            db.session.add(evaluation)
            db.session.commit()
            
            if current_user.is_irregular:
                log_action('SUBMIT_CLASS_EVALUATION', f'Irregular student {current_user.username} submitted evaluation for class {class_id} - {class_assignment.subject_name}')
            else:
                log_action('SUBMIT_CLASS_EVALUATION', f'Regular student {current_user.username} submitted evaluation for class {class_id} - {class_assignment.subject_name}')
            
            flash('Evaluation submitted successfully! Thank you for your feedback.', 'success')
            return redirect(url_for('student_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your evaluation. Please try again.', 'danger')
            app.logger.error(f"Class evaluation submission error: {str(e)}")
    
    return render_template('student/evaluate_class.html', class_assignment=class_assignment)

@app.route('/section/<int:section_id>/dashboard')
@login_required
def section_dashboard(section_id):
    """View dashboard for a specific section"""
    section = Section.query.get_or_404(section_id)
    
    if current_user.role == 'student':
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            section_id=section_id,
            is_active=True
        ).first()
        if not enrollment:
            abort(403)
    
    class_assignments = ClassAssignment.query.filter_by(section_id=section_id, is_active=True).all()
    
    class_stats = []
    for ca in class_assignments:
        evaluations = ClassEvaluation.query.filter_by(class_assignment_id=ca.id).all()
        if evaluations:
            avg_score = sum(e.calculate_raw_score() for e in evaluations) / len(evaluations)
            eval_count = len(evaluations)
        else:
            avg_score = 0
            eval_count = 0
        
        user_evaluated = False
        if current_user.is_authenticated and current_user.role == 'student':
            user_evaluated = ClassEvaluation.query.filter_by(
                class_assignment_id=ca.id,
                evaluator_id=current_user.id
            ).first() is not None
        
        class_stats.append({
            'class': ca,
            'avg_score': round(avg_score, 2),
            'eval_count': eval_count,
            'user_evaluated': user_evaluated
        })
    
    return render_template('shared/section_dashboard.html', 
                         section=section, 
                         class_stats=class_stats)

@app.route('/api/section/<int:section_id>/stats')
@login_required
def api_section_stats(section_id):
    """Get statistics for a section"""
    section = Section.query.get_or_404(section_id)
    class_assignments = ClassAssignment.query.filter_by(section_id=section_id, is_active=True).all()
    
    stats = {
        'section_name': section.name,
        'program': section.program,
        'year_level': section.year_level,
        'total_classes': len(class_assignments),
        'total_evaluations': 0,
        'average_score': 0,
        'classes': []
    }
    
    total_score = 0
    for ca in class_assignments:
        evaluations = ClassEvaluation.query.filter_by(class_assignment_id=ca.id).all()
        eval_count = len(evaluations)
        
        if eval_count > 0:
            class_avg = sum(e.calculate_raw_score() for e in evaluations) / eval_count
        else:
            class_avg = 0
        
        stats['classes'].append({
            'id': ca.id,
            'subject_name': ca.subject_name,
            'teacher_name': ca.teacher.name,
            'subject_type': ca.subject_type,
            'schedule_id': ca.schedule_id,
            'avg_score': round(class_avg, 2),
            'eval_count': eval_count
        })
        
        stats['total_evaluations'] += eval_count
        total_score += class_avg
    
    if class_assignments:
        stats['average_score'] = round(total_score / len(class_assignments), 2)
    
    return jsonify(stats)

@app.route('/check-student-id')
def check_student_id():
    """Check if student ID is available"""
    student_id = request.args.get('student_id', '').strip()
    
    if not student_id:
        return jsonify({'available': False, 'message': 'Student ID required'})
    
    if len(student_id) < 5:
        return jsonify({'available': False, 'message': 'Student ID must be at least 5 characters'})
    
    if len(student_id) > 20:
        return jsonify({'available': False, 'message': 'Student ID must be at most 20 characters'})
    
    user = User.query.filter_by(roll_number=student_id).first()
    if user:
        return jsonify({'available': False, 'message': 'Student ID already registered'})
    
    return jsonify({'available': True, 'message': 'Student ID available'})

@app.route('/check-fullname')
def check_fullname():
    """Check if full name is available"""
    fullname = request.args.get('fullname', '').strip()
    
    if not fullname:
        return jsonify({'available': False, 'message': 'Name required'})
    
    if len(fullname) < 2:
        return jsonify({'available': False, 'message': 'Name must be at least 2 characters'})
    
    if len(fullname) > 100:
        return jsonify({'available': False, 'message': 'Name must be at most 100 characters'})
    
    if not re.match(r'^[a-zA-Z\s\-\',.]+$', fullname):
        return jsonify({'available': False, 'message': 'Name can only contain letters, spaces, hyphens, apostrophes, commas, and periods'})
    
    user = User.query.filter_by(full_name=fullname).first()
    if user:
        return jsonify({'available': False, 'message': 'This name is already registered'})
    
    return jsonify({'available': True, 'message': 'Name available'})

# CLI Commands
@app.cli.command("init-db")
def init_db():
    """Initialize the database with sample data"""
    db.create_all()
    
    # Create admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@university.edu',
            full_name='System Administrator',
            role='admin',
            department='Administration'
        )
        admin.set_password('admin123')
        db.session.add(admin)
    
    # Create sample users
    users = [
        User(username='ph_cs', email='ph.cs@university.edu', 
             full_name='Dr. James Wilson', role='program_head',
             department='Computer Science'),
        User(username='dean', email='dean@university.edu', 
             full_name='Dr. Wilma Caridad C. Tolentino', role='dean',
             department='Academic Affairs'),
    ]
    
    for user in users:
        if not User.query.filter_by(username=user.username).first():
            user.set_password('password123')
            db.session.add(user)
    
    
    db.session.commit()
    print("Database initialized with sample data!")
    print("\nDefault Users:")
    print("Admin - username: admin, password: admin123")
    print("Student - username: student1, password: password123")
    print("Program Head - username: ph_cs, password: password123")
    print("Dean - username: dean, password: password123")

# ============================================
# IRREGULAR STUDENT EVALUATION ROUTE
# ============================================

@app.route('/student/evaluate-by-schedule')
@login_required
@role_required('student')
def irregular_evaluate_by_schedule():
    """Allow irregular students to evaluate a class by Schedule ID"""
    schedule_id = request.args.get('schedule_id', '').strip()
    
    if not schedule_id:
        flash('Please enter a Schedule ID.', 'warning')
        return redirect(url_for('student_dashboard'))
    
    # Validate schedule_id format (should be 5 digits)
    if not schedule_id.isdigit() or len(schedule_id) != 5:
        flash('Schedule ID must be a 5-digit number.', 'danger')
        return redirect(url_for('student_dashboard'))
    
    # Find class assignment by schedule_id
    class_assignment = ClassAssignment.query.filter_by(
        schedule_id=schedule_id,
        is_active=True
    ).first()
    
    if not class_assignment:
        flash(f'No class found with Schedule ID: {schedule_id}. Please check and try again.', 'danger')
        return redirect(url_for('student_dashboard'))
    
    # Check if already evaluated
    existing = ClassEvaluation.query.filter_by(
        class_assignment_id=class_assignment.id,
        evaluator_id=current_user.id
    ).first()
    
    if existing:
        flash(f'You have already evaluated {class_assignment.subject_name} (Schedule ID: {schedule_id}).', 'warning')
        return redirect(url_for('student_dashboard'))
    
    # Redirect to evaluation page
    flash(f'Found class: {class_assignment.subject_name} - {class_assignment.teacher.name}. Please complete your evaluation.', 'success')
    return redirect(url_for('student_evaluate_class', class_id=class_assignment.id))

if __name__ == '__main__':
    app.run(debug=True)