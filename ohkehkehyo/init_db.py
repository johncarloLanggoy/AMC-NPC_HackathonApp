# init_db.py
from app import app
from models import db, User, Teacher, Program, Evaluation, AuditLog, EmailReminder
from datetime import datetime
from werkzeug.security import generate_password_hash

def init_database():
    with app.app_context():
        # Drop all tables (optional - be careful with this in production!)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@university.edu',
            full_name='System Administrator',
            role='admin',
            department='Administration',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create sample teachers
        teachers = [
            Teacher(name='Dr. John Smith', email='john.smith@university.edu', 
                    department='Computer Science', subjects='Programming, Algorithms, Data Structures'),
            Teacher(name='Prof. Sarah Johnson', email='sarah.johnson@university.edu', 
                    department='Mathematics', subjects='Calculus, Linear Algebra, Statistics'),
            Teacher(name='Dr. Emily Brown', email='emily.brown@university.edu', 
                    department='Physics', subjects='Mechanics, Quantum Physics, Thermodynamics'),
            Teacher(name='Prof. David Wilson', email='david.wilson@university.edu', 
                    department='English', subjects='Literature, Composition, Creative Writing'),
        ]
        
        for teacher in teachers:
            db.session.add(teacher)
        
        # Create sample users
        users = [
            User(username='student1', email='student1@university.edu', 
                 full_name='Alice Wonder', role='student', 
                 roll_number='STU001', program='Computer Science', semester=3),
            User(username='student2', email='student2@university.edu', 
                 full_name='Bob Builder', role='student',
                 roll_number='STU002', program='Mathematics', semester=5),
            User(username='student3', email='student3@university.edu', 
                 full_name='Charlie Brown', role='student',
                 roll_number='STU003', program='Physics', semester=3),
            User(username='ph_cs', email='ph.cs@university.edu', 
                 full_name='Dr. James Wilson', role='program_head',
                 department='Computer Science'),
            User(username='ph_math', email='ph.math@university.edu', 
                 full_name='Dr. Lisa Anderson', role='program_head',
                 department='Mathematics'),
            User(username='dean', email='dean@university.edu', 
                 full_name='Dr. Robert Taylor', role='dean',
                 department='Academic Affairs'),
        ]
        
        for user in users:
            user.set_password('password123')
            db.session.add(user)
        
        # Create sample programs
        programs = [
            Program(name='Bachelor of Science in Computer Science', department='Computer Science'),
            Program(name='Bachelor of Science in Mathematics', department='Mathematics'),
            Program(name='Bachelor of Science in Physics', department='Physics'),
            Program(name='Bachelor of Arts in English', department='English'),
        ]
        
        for program in programs:
            db.session.add(program)
        
        # Commit all changes
        db.session.commit()
        
        print("=" * 50)
        print("Database initialized successfully!")
        print("=" * 50)
        print("\nCreated tables:")
        print("- users")
        print("- teachers")
        print("- programs")
        print("- evaluations")
        print("- audit_logs")
        print("- email_reminders")
        print("\nSample users created:")
        print("- Admin: admin / admin123")
        print("- Student: student1 / password123")
        print("- Program Head: ph_cs / password123")
        print("- Dean: dean / password123")
        print("\n" + "=" * 50)

if __name__ == '__main__':
    init_database()