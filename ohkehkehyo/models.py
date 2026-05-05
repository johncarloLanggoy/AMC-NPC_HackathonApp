from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # student, program_head, dean, admin
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Student specific
    roll_number = db.Column(db.String(20), unique=True)
    program = db.Column(db.String(100))
    semester = db.Column(db.Integer)
    is_irregular = db.Column(db.Boolean, default=False)  # ADDED: Regular/Irregular student
    
    # Relationships
    evaluations_given = db.relationship('Evaluation', foreign_keys='Evaluation.evaluator_id', 
                                      backref='evaluator', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)
    class_evaluations = db.relationship('ClassEvaluation', backref='evaluator', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    subjects = db.Column(db.String(500))  # Comma-separated subjects
    joining_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    evaluations = db.relationship('Evaluation', backref='teacher', lazy=True)
    class_assignments = db.relationship('ClassAssignment', backref='teacher', lazy=True)
    
    def __repr__(self):
        return f'<Teacher {self.name}>'


class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    evaluator_role = db.Column(db.String(50), nullable=False)
    
    # Student evaluation criteria (50% weight)
    teaching_clarity = db.Column(db.Integer)  # 1-5
    engagement = db.Column(db.Integer)  # 1-5
    fairness = db.Column(db.Integer)  # 1-5
    
    # Program Head evaluation criteria (30% weight)
    curriculum_implementation = db.Column(db.Integer)  # 1-5
    assessment_quality = db.Column(db.Integer)  # 1-5
    mentoring = db.Column(db.Integer)  # 1-5
    
    # Dean evaluation criteria (20% weight)
    attendance = db.Column(db.Integer)  # 1-5
    commitment = db.Column(db.Integer)  # 1-5
    teaching_quality = db.Column(db.Integer)  # 1-5
    
    comments = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_anonymous = db.Column(db.Boolean, default=True)
    
    @property
    def _weight(self):
        weights = {'student': 0.5, 'program_head': 0.3, 'dean': 0.2}
        return weights.get(self.evaluator_role, 0)
    
    def calculate_raw_score(self):
        """Calculate raw average score (1-5 scale)"""
        if self.evaluator_role == 'student':
            scores = [self.teaching_clarity, self.engagement, self.fairness]
        elif self.evaluator_role == 'program_head':
            scores = [self.curriculum_implementation, self.assessment_quality, self.mentoring]
        elif self.evaluator_role == 'dean':
            scores = [self.attendance, self.commitment, self.teaching_quality]
        else:
            return 0
        
        valid_scores = [s for s in scores if s is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0
    
    def calculate_weighted_score(self):
        """Calculate weighted score based on role weight"""
        raw_score = self.calculate_raw_score()
        return round(raw_score * self._weight, 2)
    
    def __repr__(self):
        return f'<Evaluation {self.id}: Teacher {self.teacher_id}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.action}>'


class Program(db.Model):
    __tablename__ = 'programs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    coordinator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    coordinator = db.relationship('User', foreign_keys=[coordinator_id])
    teachers = db.relationship('Teacher', secondary='program_teachers', 
                             backref=db.backref('programs', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Program {self.name}>'


program_teachers = db.Table('program_teachers',
    db.Column('program_id', db.Integer, db.ForeignKey('programs.id'), primary_key=True),
    db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id'), primary_key=True)
)


class EmailReminder(db.Model):
    __tablename__ = 'email_reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(db.String(120), nullable=False)
    recipient_role = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime)
    scheduled_for = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailReminder {self.id}: {self.recipient_email}>'


# NEW MODELS FOR SECTION-BASED EVALUATION

class Section(db.Model):
    __tablename__ = 'sections'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    program = db.Column(db.String(100), nullable=False)
    year_level = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer, default=1)
    school_year = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    class_assignments = db.relationship('ClassAssignment', backref='section', lazy=True, cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='section', lazy=True)
    
    def __repr__(self):
        return f'<Section {self.name}>'


class ClassAssignment(db.Model):
    __tablename__ = 'class_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    subject_name = db.Column(db.String(200), nullable=False)
    subject_type = db.Column(db.String(20), default='LEC')
    schedule_id = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    evaluations = db.relationship('ClassEvaluation', backref='class_assignment', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ClassAssignment {self.subject_name} - {self.schedule_id}>'


class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'section_id', name='unique_student_section'),)
    
    def __repr__(self):
        return f'<Enrollment Student:{self.student_id} Section:{self.section_id}>'


class ClassEvaluation(db.Model):
    __tablename__ = 'class_evaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    class_assignment_id = db.Column(db.Integer, db.ForeignKey('class_assignments.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Evaluation criteria (1-5 scale)
    teaching_clarity = db.Column(db.Integer, nullable=False)
    engagement = db.Column(db.Integer, nullable=False)
    fairness = db.Column(db.Integer, nullable=False)
    subject_mastery = db.Column(db.Integer, nullable=False)
    punctuality = db.Column(db.Integer, nullable=False)
    
    comments = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_anonymous = db.Column(db.Boolean, default=True)
    
    def calculate_raw_score(self):
        """Calculate average score (1-5 scale)"""
        scores = [self.teaching_clarity, self.engagement, self.fairness, 
                  self.subject_mastery, self.punctuality]
        return sum(scores) / len(scores)
    
    def __repr__(self):
        return f'<ClassEvaluation {self.id}>'