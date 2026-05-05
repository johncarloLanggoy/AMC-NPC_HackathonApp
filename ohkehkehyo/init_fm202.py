# init_fm202.py
from app import app
from models import db, User, Teacher, Section, ClassAssignment, Enrollment
from datetime import datetime

def init_fm202():
    with app.app_context():
        print("=" * 60)
        print("Initializing FM 202 Section")
        print("=" * 60)
        
        # Create or get section
        section = Section.query.filter_by(name='FM 202').first()
        if not section:
            section = Section(
                name='FM 202',
                program='Bachelor of Science in Financial Management',
                year_level=2,
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
            {'name': 'Evelyn Tanganoan', 'email': 'evelyn.tanganoan@university.edu', 
             'department': 'Entrepreneurship', 'subjects': 'The Entrepreneurial Mind'},
            {'name': 'Mario Camacho', 'email': 'mario.camacho@university.edu', 
             'department': 'Financial Management', 'subjects': 'Financial Analysis and Reporting'},
            {'name': 'Neil Bibal', 'email': 'neil.bibal@university.edu', 
             'department': 'Business Administration', 'subjects': 'International Business and Trade'},
            {'name': 'Mariel Prado', 'email': 'mariel.prado@university.edu', 
             'department': 'Business Administration', 'subjects': 'Leadership 4'},
            {'name': 'Daisy Cuadra', 'email': 'daisy.cuadra@university.edu', 
             'department': 'Arts and Humanities', 'subjects': 'Art Appreciation'},
            {'name': 'Mary Shane Carpila', 'email': 'mary.carpila@university.edu', 
             'department': 'Social Sciences', 'subjects': 'Sosyedad at Literatura'},
            {'name': 'Vevencio Gabuya Jr.', 'email': 'vevencio.gabuya@university.edu', 
             'department': 'Physical Education', 'subjects': 'Pathfit 4'},
            {'name': 'Jabez Espiritu', 'email': 'jabez.espiritu@university.edu', 
             'department': 'Business Administration', 'subjects': 'Human Resource Management'},
            {'name': 'Leandro Tulod', 'email': 'leandro.tulod@university.edu', 
             'department': 'Accountancy', 'subjects': 'Taxation'},
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
        
        # Create class assignments for FM 202 with generated schedule IDs
        class_assignments_data = [
            {'teacher_name': 'Evelyn Tanganoan', 'subject': 'THE ENTREPRENEURIAL MIND', 'schedule_id': '50201', 'subject_type': 'LEC'},
            {'teacher_name': 'Mario Camacho', 'subject': 'FINANCIAL ANALYSIS AND REPORTING', 'schedule_id': '50202', 'subject_type': 'LEC'},
            {'teacher_name': 'Neil Bibal', 'subject': 'INTERNATIONAL BUSINESS AND TRADE', 'schedule_id': '50203', 'subject_type': 'LEC'},
            {'teacher_name': 'Mariel Prado', 'subject': 'LEADERSHIP 4', 'schedule_id': '50204', 'subject_type': 'LEC'},
            {'teacher_name': 'Daisy Cuadra', 'subject': 'ART APPRECIATION', 'schedule_id': '50205', 'subject_type': 'LEC'},
            {'teacher_name': 'Mary Shane Carpila', 'subject': 'SOSYEDAD AT LITERATURA', 'schedule_id': '50206', 'subject_type': 'LEC'},
            {'teacher_name': 'Vevencio Gabuya Jr.', 'subject': 'PATHFIT 4', 'schedule_id': '50207', 'subject_type': 'LAB'},
            {'teacher_name': 'Jabez Espiritu', 'subject': 'HUMAN RESOURCE MANAGEMENT', 'schedule_id': '50208', 'subject_type': 'LEC'},
            {'teacher_name': 'Leandro Tulod', 'subject': 'TAXATION', 'schedule_id': '50209', 'subject_type': 'LEC'},
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
                    print(f"Added class: {ca_data['subject']} ({ca_data['schedule_id']}) - {teacher.name}")
                else:
                    print(f"Class already exists: {ca_data['subject']}")
        
        db.session.commit()
        
        # Create sample student users for FM 202
        sample_students = [
            {'username': 'fm202_student1', 'full_name': 'Warren Buffett', 'roll_number': '2024-FM-0001'},
            {'username': 'fm202_student2', 'full_name': 'Peter Lynch', 'roll_number': '2024-FM-0002'},
            {'username': 'fm202_student3', 'full_name': 'Benjamin Graham', 'roll_number': '2024-FM-0003'},
            {'username': 'fm202_student4', 'full_name': 'Ray Dalio', 'roll_number': '2024-FM-0004'},
            {'username': 'fm202_student5', 'full_name': 'Catherine Wood', 'roll_number': '2024-FM-0005'},
        ]
        
        for s_data in sample_students:
            student = User.query.filter_by(username=s_data['username']).first()
            if not student:
                student = User(
                    username=s_data['username'],
                    email=f"{s_data['username']}@student.university.edu",
                    full_name=s_data['full_name'],
                    role='student',
                    department='Financial Management',
                    roll_number=s_data['roll_number'],
                    program='Bachelor of Science in Financial Management',
                    semester=2,
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
        print("FM 202 SECTION INITIALIZED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\nSection: {section.name}")
        print(f"Program: {section.program}")
        print(f"Year Level: {section.year_level}")
        print(f"Total Class Assignments: {ClassAssignment.query.filter_by(section_id=section.id).count()}")
        print(f"Total Students Enrolled: {Enrollment.query.filter_by(section_id=section.id).count()}")
        
        print("\n" + "-" * 40)
        print("CLASS ASSIGNMENTS FOR FM 202:")
        print("-" * 40)
        classes = ClassAssignment.query.filter_by(section_id=section.id, is_active=True).all()
        for ca in classes:
            print(f"  {ca.subject_name}")
            print(f"    Teacher: {ca.teacher.name}")
            print(f"    Schedule ID: {ca.schedule_id}")
            print(f"    Type: {ca.subject_type}")
            print()
        
        print("\n" + "=" * 60)
        print("STUDENT LOGINS:")
        print("=" * 60)
        for s_data in sample_students:
            print(f"  Username: {s_data['username']}, Password: password123")
        
        print("\nADMIN LOGIN:")
        print("  Username: admin, Password: admin123")
        
        print("\nPROGRAM HEAD (ONLY):")
        print("  Username: ph_cs, Password: password123")
        
        print("\n" + "=" * 60)

if __name__ == '__main__':
    init_fm202()