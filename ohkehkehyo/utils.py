from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import csv
import io
from datetime import datetime, timedelta
from flask_mail import Message
from flask import url_for, current_app
import threading
import pandas as pd

# Import models at the top
from models import Teacher, Evaluation

def generate_pdf_report(teacher_data, evaluations):
    """Generate PDF report for a teacher"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#34495e')
    )
    
    # Title
    elements.append(Paragraph("Teacher Evaluation Report", title_style))
    elements.append(Spacer(1, 12))
    
    # Teacher Info
    elements.append(Paragraph(f"Teacher: {teacher_data['name']}", styles['Normal']))
    elements.append(Paragraph(f"Department: {teacher_data['department']}", styles['Normal']))
    elements.append(Paragraph(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Paragraph(f"Total Evaluations: {teacher_data['total_evaluations']}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Summary Table
    elements.append(Paragraph("Evaluation Summary", heading_style))
    summary_data = [['Role', 'Average Score', 'Weighted Contribution', 'Number of Evaluations']]
    
    for role, data in teacher_data['scores_by_role'].items():
        summary_data.append([
            role.replace('_', ' ').title(),
            f"{data['avg']:.2f}",
            f"{data['weighted']:.2f}",
            str(data['count'])
        ])
    
    summary_data.append(['TOTAL', '', f"{teacher_data['final_score']:.2f}", ''])
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1.8*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Detailed Evaluations
    elements.append(Paragraph("Recent Evaluations", heading_style))
    
    for eval in evaluations[:20]:  # Show last 20 evaluations
        eval_data = [
            [f"Date: {eval['submitted_at'].strftime('%Y-%m-%d %H:%M')}"],
            [f"Evaluator Role: {eval['evaluator_role'].replace('_', ' ').title()}"],
            [f"Raw Score: {eval['raw_score']:.2f} / 5.00"],
            [f"Weighted Score: {eval['weighted_score']:.2f}"],
        ]
        if eval['comments']:
            eval_data.append([f"Comments: {eval['comments']}"])
        
        eval_table = Table(eval_data, colWidths=[6.5*inch])
        eval_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -2), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ]))
        elements.append(eval_table)
        elements.append(Spacer(1, 15))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_csv_report(teacher_data, evaluations):
    """Generate CSV report for a teacher"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Teacher Evaluation Report'])
    writer.writerow([])
    writer.writerow(['Teacher Information'])
    writer.writerow(['Name:', teacher_data['name']])
    writer.writerow(['Department:', teacher_data['department']])
    writer.writerow(['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['Total Evaluations:', teacher_data['total_evaluations']])
    writer.writerow([])
    
    # Write summary by role
    writer.writerow(['Summary by Role'])
    writer.writerow(['Role', 'Average Score', 'Weighted Contribution', 'Number of Evaluations'])
    for role, data in teacher_data['scores_by_role'].items():
        writer.writerow([
            role.replace('_', ' ').title(),
            f"{data['avg']:.2f}",
            f"{data['weighted']:.2f}",
            data['count']
        ])
    writer.writerow(['TOTAL', '', f"{teacher_data['final_score']:.2f}", ''])
    writer.writerow([])
    
    # Write detailed evaluations
    writer.writerow(['Detailed Evaluations'])
    writer.writerow(['Date', 'Evaluator Role', 'Raw Score', 'Weighted Score', 'Comments'])
    for eval in evaluations:
        writer.writerow([
            eval['submitted_at'].strftime('%Y-%m-%d %H:%M'),
            eval['evaluator_role'].replace('_', ' ').title(),
            f"{eval['raw_score']:.2f}",
            f"{eval['weighted_score']:.2f}",
            eval['comments'] or ''
        ])
    
    output.seek(0)
    return output

def generate_audit_log_csv(audit_logs):
    """Generate CSV for audit logs"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Audit Log Report'])
    writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    writer.writerow(['Timestamp', 'User', 'Role', 'Action', 'Details', 'IP Address'])
    
    for log in audit_logs:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.full_name if log.user else 'Unknown',
            log.user.role if log.user else 'Unknown',
            log.action,
            log.details or '',
            log.ip_address or ''
        ])
    
    output.seek(0)
    return output

def send_email_async(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            from flask_mail import Mail
            mail = Mail(app)
            mail.send(msg)
            print(f"Email sent successfully to {msg.recipients}")
        except Exception as e:
            print(f"Failed to send email: {e}")

def send_reminder_email(recipient_email, recipient_name, deadline, app):
    """Send evaluation reminder email"""
    from flask import url_for
    
    msg = Message(
        subject="Teacher Evaluation Reminder",
        recipients=[recipient_email]
    )
    msg.body = f"""
    Dear {recipient_name},
    
    This is a reminder to complete your pending teacher evaluations.
    
    Deadline: {deadline.strftime('%Y-%m-%d %H:%M')}
    
    Please log in to the Teacher Evaluation System at your earliest convenience to submit your evaluations.
    
    Your feedback is valuable for improving teaching quality.
    
    Thank you for your participation.
    
    Best regards,
    Administration
    Teacher Evaluation System
    """
    
    with app.app_context():
        login_url = url_for('login', _external=True)
        
    msg.html = f"""
    <html>
    <body>
        <h3>Teacher Evaluation Reminder</h3>
        <p>Dear {recipient_name},</p>
        <p>This is a reminder to complete your pending teacher evaluations.</p>
        <p><strong>Deadline:</strong> {deadline.strftime('%Y-%m-%d %H:%M')}</p>
        <p>Please <a href="{login_url}">log in</a> to submit your evaluations.</p>
        <p>Your feedback is valuable for improving teaching quality.</p>
        <br>
        <p>Thank you for your participation.</p>
        <p>Best regards,<br>Administration<br>Teacher Evaluation System</p>
    </body>
    </html>
    """
    
    threading.Thread(target=send_email_async, args=(app, msg)).start()

def calculate_teacher_stats(teacher_id, evaluations):
    """Calculate comprehensive statistics for a teacher"""
    stats = {
        'total_evaluations': len(evaluations),
        'scores_by_role': {
            'student': {'total': 0, 'count': 0, 'scores': [], 'avg': 0},
            'program_head': {'total': 0, 'count': 0, 'scores': [], 'avg': 0},
            'dean': {'total': 0, 'count': 0, 'scores': [], 'avg': 0}
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
    
    # Temporary lists for category averages
    category_lists = {
        'teaching_clarity': [],
        'engagement': [],
        'fairness': [],
        'curriculum': [],
        'assessment': [],
        'mentoring': [],
        'attendance': [],
        'commitment': [],
        'teaching_quality': []
    }
    
    for eval in evaluations:
        role = eval.evaluator_role
        raw_score = eval.calculate_raw_score()
        
        # Update role-based stats
        stats['scores_by_role'][role]['total'] += raw_score
        stats['scores_by_role'][role]['count'] += 1
        stats['scores_by_role'][role]['scores'].append(raw_score)
        
        # Update monthly averages
        month_key = eval.submitted_at.strftime('%Y-%m')
        if month_key not in stats['monthly_averages']:
            stats['monthly_averages'][month_key] = {'total': 0, 'count': 0}
        stats['monthly_averages'][month_key]['total'] += raw_score
        stats['monthly_averages'][month_key]['count'] += 1
        
        # Update category averages
        if role == 'student':
            if eval.teaching_clarity:
                category_lists['teaching_clarity'].append(eval.teaching_clarity)
            if eval.engagement:
                category_lists['engagement'].append(eval.engagement)
            if eval.fairness:
                category_lists['fairness'].append(eval.fairness)
        elif role == 'program_head':
            if eval.curriculum_implementation:
                category_lists['curriculum'].append(eval.curriculum_implementation)
            if eval.assessment_quality:
                category_lists['assessment'].append(eval.assessment_quality)
            if eval.mentoring:
                category_lists['mentoring'].append(eval.mentoring)
        elif role == 'dean':
            if eval.attendance:
                category_lists['attendance'].append(eval.attendance)
            if eval.commitment:
                category_lists['commitment'].append(eval.commitment)
            if eval.teaching_quality:
                category_lists['teaching_quality'].append(eval.teaching_quality)
    
    # Calculate averages for roles
    for role in stats['scores_by_role']:
        if stats['scores_by_role'][role]['count'] > 0:
            stats['scores_by_role'][role]['avg'] = round(
                stats['scores_by_role'][role]['total'] / stats['scores_by_role'][role]['count'], 2
            )
    
    # Calculate monthly averages
    for month in stats['monthly_averages']:
        stats['monthly_averages'][month] = round(
            stats['monthly_averages'][month]['total'] / stats['monthly_averages'][month]['count'], 2
        )
    
    # Calculate category averages
    for category in stats['category_averages']:
        if category_lists[category]:
            stats['category_averages'][category] = round(
                sum(category_lists[category]) / len(category_lists[category]), 2
            )
    
    return stats

def check_evaluation_eligibility(user, teacher_id):
    """Check if a user is eligible to evaluate a teacher"""
    from models import Evaluation, Teacher
    
    # Check if already evaluated
    existing = Evaluation.query.filter_by(
        teacher_id=teacher_id,
        evaluator_id=user.id,
        evaluator_role=user.role
    ).first()
    
    if existing:
        return False, "You have already evaluated this teacher"
    
    # Role-specific checks
    if user.role == 'program_head':
        # Check if teacher is in same department
        teacher = Teacher.query.get(teacher_id)
        if teacher and teacher.department != user.department:
            return False, "You can only evaluate teachers in your department"
    
    return True, "Eligible"

def calculate_weighted_score(teacher_id):
    """Calculate weighted score for a teacher"""
    from models import Evaluation
    from config import Config
    
    evaluations = Evaluation.query.filter_by(teacher_id=teacher_id).all()
    
    if not evaluations:
        return 0
    
    scores_by_role = {
        'student': {'total': 0, 'count': 0},
        'program_head': {'total': 0, 'count': 0},
        'dean': {'total': 0, 'count': 0}
    }
    
    for eval in evaluations:
        role = eval.evaluator_role
        raw_score = eval.calculate_raw_score()
        scores_by_role[role]['total'] += raw_score
        scores_by_role[role]['count'] += 1
    
    weighted_score = 0
    for role, data in scores_by_role.items():
        if data['count'] > 0:
            avg = data['total'] / data['count']
            weighted_score += avg * Config.WEIGHTS[role]
    
    return round(weighted_score, 2)

def get_department_statistics(department):
    """Get statistics for a specific department"""
    from models import Teacher, Evaluation
    
    teachers = Teacher.query.filter_by(department=department, is_active=True).all()
    
    stats = {
        'total_teachers': len(teachers),
        'total_evaluations': 0,
        'average_score': 0,
        'teachers': []
    }
    
    total_score = 0
    for teacher in teachers:
        evaluations = Evaluation.query.filter_by(teacher_id=teacher.id).all()
        eval_count = len(evaluations)
        
        if eval_count > 0:
            teacher_avg = sum(e.calculate_raw_score() for e in evaluations) / eval_count
        else:
            teacher_avg = 0
        
        stats['teachers'].append({
            'id': teacher.id,
            'name': teacher.name,
            'evaluations': eval_count,
            'average_score': round(teacher_avg, 2)
        })
        
        stats['total_evaluations'] += eval_count
        total_score += teacher_avg
    
    if teachers:
        stats['average_score'] = round(total_score / len(teachers), 2)
    
    return stats

def get_program_statistics(program_id):
    """Get statistics for a specific program"""
    from models import Program, Evaluation
    
    program = Program.query.get(program_id)
    if not program:
        return None
    
    teachers = program.teachers
    
    stats = {
        'program_name': program.name,
        'department': program.department,
        'total_teachers': len(teachers),
        'total_evaluations': 0,
        'average_score': 0,
        'teachers': []
    }
    
    total_score = 0
    for teacher in teachers:
        evaluations = Evaluation.query.filter_by(teacher_id=teacher.id).all()
        eval_count = len(evaluations)
        
        if eval_count > 0:
            teacher_avg = sum(e.calculate_raw_score() for e in evaluations) / eval_count
        else:
            teacher_avg = 0
        
        stats['teachers'].append({
            'id': teacher.id,
            'name': teacher.name,
            'evaluations': eval_count,
            'average_score': round(teacher_avg, 2)
        })
        
        stats['total_evaluations'] += eval_count
        total_score += teacher_avg
    
    if teachers:
        stats['average_score'] = round(total_score / len(teachers), 2)
    
    return stats