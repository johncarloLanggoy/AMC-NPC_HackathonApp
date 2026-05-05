# init_bsit307.py
from app import app
from models import db, User, Teacher, Section, ClassAssignment, Enrollment
from datetime import datetime

def init_bsit307():
    with app.app_context():
        print("=" * 60)
        print("Initializing BSIT 307 Section")
        print("=" * 60)
        
        # Create or get section
        section = Section.query.filter_by(name='BSIT 307').first()
        if not section:
            section = Section(
                name='BSIT 307',
                program='Bachelor of Science in Information Technology',
                year_level=3,
                semester=1,
                school_year='2025-2026',
                is_active=True
            )
            db.session.add(section)
            db.session.commit()
            print(f"Created section: {section.name}")
        else:
            print(f"Section already exists: {section.name}")
        
        # Create teachers based on your data
        teachers_data = [
            {'name': 'Cacho Romark', 'email': 'romark.cacho@university.edu', 
             'department': 'Information Technology', 'subjects': 'Advance Mobile Computing'},
            {'name': 'Christian Esguerra', 'email': 'christian.esguerra@university.edu', 
             'department': 'Information Technology', 'subjects': 'Computer Architecture and Organization'},
            {'name': 'Dong Rodrigo', 'email': 'dong.rodrigo@university.edu', 
             'department': 'Information Technology', 'subjects': 'Capstone Project and Research 1'},
            {'name': 'Rhavee Valencia', 'email': 'rhavee.valencia@university.edu', 
             'department': 'Information Technology', 'subjects': 'Information Assurance and Security 1'},
            {'name': 'Jude Thaddeus', 'email': 'jude.thaddeus@university.edu', 
             'department': 'Information Technology', 'subjects': 'Leadership 6'},
            {'name': 'Ann Camile M. Maupay', 'email': 'ann.maupay@university.edu', 
             'department': 'Information Technology', 'subjects': 'Quantitative Methods'},
            {'name': 'Maria Maritess Olvis', 'email': 'maritess.olvis@university.edu', 
             'department': 'Information Technology', 'subjects': "Rizal's Life and Works"},
            {'name': 'Mark Gabriel Antipala', 'email': 'mark.antipala@university.edu', 
             'department': 'Information Technology', 'subjects': 'Web System and Technologies'},
        ]
        
        teachers = {}
        for t_data in teachers_data:
            teacher = Teacher.query.filter_by(email=t_data['email']).first()
            if not teacher:
                teacher = Teacher(
                    name=t_data['name'],
                    email=t_data['email'],
                    department=t_data['department'],
                    subjects=t_data['subjects'],
                    is_active=True
                )
                db.session.add(teacher)
                db.session.commit()
                print(f"Created teacher: {teacher.name}")
            else:
                print(f"Teacher already exists: {teacher.name}")
            teachers[t_data['name']] = teacher
        
        # Create class assignments for BSIT 307 based on your data
        class_assignments_data = [
            {'teacher_name': 'Cacho Romark', 'subject': 'ADVANCE MOBILE COMPUTING LEC', 'schedule_id': '37141', 'subject_type': 'LEC'},
            {'teacher_name': 'Cacho Romark', 'subject': 'ADVANCE MOBILE COMPUTING LAB', 'schedule_id': '37139', 'subject_type': 'LAB'},
            {'teacher_name': 'Christian Esguerra', 'subject': 'COMPUTER ARCHITECTURE AND ORGANIZATION LEC', 'schedule_id': '37149', 'subject_type': 'LEC'},
            {'teacher_name': 'Christian Esguerra', 'subject': 'COMPUTER ARCHITECTURE AND ORGANIZATION LAB', 'schedule_id': '37151', 'subject_type': 'LAB'},
            {'teacher_name': 'Dong Rodrigo', 'subject': 'CAPSTONE PROJECT AND RESEARCH 1 LEC', 'schedule_id': '37145', 'subject_type': 'LEC'},
            {'teacher_name': 'Dong Rodrigo', 'subject': 'CAPSTONE PROJECT AND RESEARCH 1 LAB', 'schedule_id': '37145', 'subject_type': 'LAB'},
            {'teacher_name': 'Rhavee Valencia', 'subject': 'INFORMATION ASSURANCE AND SECURITY 1 LEC', 'schedule_id': '37135', 'subject_type': 'LEC'},
            {'teacher_name': 'Rhavee Valencia', 'subject': 'INFORMATION ASSURANCE AND SECURITY 1 LAB', 'schedule_id': '37137', 'subject_type': 'LAB'},
            {'teacher_name': 'Jude Thaddeus', 'subject': 'LEADERSHIP 6', 'schedule_id': '37157', 'subject_type': 'LEC'},
            {'teacher_name': 'Ann Camile M. Maupay', 'subject': 'QUANTITATIVE METHODS (MODELING AND SIMULATION)', 'schedule_id': '37159', 'subject_type': 'LEC'},
            {'teacher_name': 'Maria Maritess Olvis', 'subject': "RIZAL'S LIFE AND WORKS", 'schedule_id': '37147', 'subject_type': 'LEC'},
            {'teacher_name': 'Mark Gabriel Antipala', 'subject': 'WEB SYSTEM AND TECHNOLOGIES LEC', 'schedule_id': '37155', 'subject_type': 'LEC'},
            {'teacher_name': 'Mark Gabriel Antipala', 'subject': 'WEB SYSTEM AND TECHNOLOGIES LAB', 'schedule_id': '37153', 'subject_type': 'LAB'},
        ]
        
        for ca_data in class_assignments_data:
            teacher = teachers.get(ca_data['teacher_name'])
            if teacher:
                existing = ClassAssignment.query.filter_by(
                    section_id=section.id,
                    teacher_id=teacher.id,
                    schedule_id=ca_data['schedule_id']
                ).first()
                
                if not existing:
                    class_assignment = ClassAssignment(
                        section_id=section.id,
                        teacher_id=teacher.id,
                        subject_name=ca_data['subject'],
                        subject_type=ca_data['subject_type'],
                        schedule_id=ca_data['schedule_id'],
                        is_active=True
                    )
                    db.session.add(class_assignment)
                    print(f"Added class: {ca_data['subject']} ({ca_data['schedule_id']})")
                else:
                    print(f"Class already exists: {ca_data['subject']}")
        
        db.session.commit()
        
        # Create sample student users for BSIT 307
        sample_students = [
            {'username': 'bsit307_student1', 'full_name': 'Juan Dela Cruz', 'roll_number': '2023-IT-0001'},
            {'username': 'bsit307_student2', 'full_name': 'Maria Santos', 'roll_number': '2023-IT-0002'},
            {'username': 'bsit307_student3', 'full_name': 'Jose Rizal', 'roll_number': '2023-IT-0003'},
        ]
        
        for s_data in sample_students:
            student = User.query.filter_by(username=s_data['username']).first()
            if not student:
                student = User(
                    username=s_data['username'],
                    email=f"{s_data['username']}@student.university.edu",
                    full_name=s_data['full_name'],
                    role='student',
                    department='Information Technology',
                    roll_number=s_data['roll_number'],
                    program='Bachelor of Science in Information Technology',
                    semester=1,
                    is_active=True
                )
                student.set_password('password123')
                db.session.add(student)
                db.session.commit()
                print(f"Created student: {student.username} - {student.full_name}")
            else:
                print(f"Student already exists: {student.username}")
            
            # Enroll student in section
            existing_enrollment = Enrollment.query.filter_by(
                student_id=student.id,
                section_id=section.id
            ).first()
            
            if not existing_enrollment:
                enrollment = Enrollment(
                    student_id=student.id,
                    section_id=section.id,
                    is_active=True
                )
                db.session.add(enrollment)
                print(f"Enrolled {student.full_name} in {section.name}")
            else:
                print(f"{student.full_name} already enrolled in {section.name}")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("BSIT 307 SECTION INITIALIZED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\nSection: {section.name}")
        print(f"Total Class Assignments: {ClassAssignment.query.filter_by(section_id=section.id).count()}")
        print(f"Total Students Enrolled: {Enrollment.query.filter_by(section_id=section.id).count()}")
        print("\nSample Student Logins:")
        print("  Username: bsit307_student1, Password: password123")
        print("  Username: bsit307_student2, Password: password123")
        print("  Username: bsit307_student3, Password: password123")
        print("\nAdmin login: admin / admin123")
        print("\n" + "=" * 60)

if __name__ == '__main__':
    init_bsit307()