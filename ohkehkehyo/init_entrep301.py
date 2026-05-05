# init_entrep301.py
from app import app
from models import db, User, Teacher, Section, ClassAssignment, Enrollment
from datetime import datetime

def init_entrep301():
    with app.app_context():
        print("=" * 60)
        print("Initializing ENTREP 301 Section")
        print("=" * 60)
        
        # Create or get section
        section = Section.query.filter_by(name='ENTREP 301').first()
        if not section:
            section = Section(
                name='ENTREP 301',
                program='Bachelor of Science in Entrepreneurship',
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
            {'name': 'Evelyn Tanangonan', 'email': 'evelyn.tanangonan@university.edu', 
             'department': 'Hospitality and Tourism Business', 'subjects': 'Hospitality and Tourism Business'},
            {'name': 'Joseph Briola', 'email': 'joseph.briola@university.edu', 
             'department': 'Financial Management', 'subjects': 'Financial Management'},
            {'name': 'Shiela SanJuan', 'email': 'shiela.sanjuan@university.edu', 
             'department': 'Business Administration', 'subjects': 'Business Plan Preparation'},
            {'name': 'Teodoro Canay', 'email': 'teodoro.canay@university.edu', 
             'department': 'Business Administration', 'subjects': 'Microfinance, E Commerce and Internet Marketing'},
            {'name': 'David Ryan Tolentino', 'email': 'david.tolentino@university.edu', 
             'department': 'Business Administration', 'subjects': 'Strategic Management'},
            {'name': 'Jay R Loreto', 'email': 'jay.loreto@university.edu', 
             'department': 'Business Administration', 'subjects': 'Leadership 6'},
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
        
        # Create class assignments for ENTREP 301 with generated schedule IDs
        class_assignments_data = [
            {'teacher_name': 'Evelyn Tanangonan', 'subject': 'HOSPITALITY AND TOURISM BUSINESS', 'schedule_id': '50101', 'subject_type': 'LEC'},
            {'teacher_name': 'Joseph Briola', 'subject': 'FINANCIAL MANAGEMENT', 'schedule_id': '50102', 'subject_type': 'LEC'},
            {'teacher_name': 'Shiela SanJuan', 'subject': 'BUSINESS PLAN PREPARATION', 'schedule_id': '50103', 'subject_type': 'LEC'},
            {'teacher_name': 'Teodoro Canay', 'subject': 'MICROFINANCE', 'schedule_id': '50104', 'subject_type': 'LEC'},
            {'teacher_name': 'David Ryan Tolentino', 'subject': 'STRATEGIC MANAGEMENT', 'schedule_id': '50105', 'subject_type': 'LEC'},
            {'teacher_name': 'Teodoro Canay', 'subject': 'E COMMERCE AND INTERNET MARKETING', 'schedule_id': '50106', 'subject_type': 'LEC'},
            {'teacher_name': 'Jay R Loreto', 'subject': 'LEADERSHIP 6', 'schedule_id': '50107', 'subject_type': 'LEC'},
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
        
        # Create sample student users for ENTREP 301
        sample_students = [
            {'username': 'entrep301_student1', 'full_name': 'Mark Zuckerberg', 'roll_number': '2023-ENT-0001'},
            {'username': 'entrep301_student2', 'full_name': 'Sara Blakely', 'roll_number': '2023-ENT-0002'},
            {'username': 'entrep301_student3', 'full_name': 'Elon Musk', 'roll_number': '2023-ENT-0003'},
            {'username': 'entrep301_student4', 'full_name': 'Oprah Winfrey', 'roll_number': '2023-ENT-0004'},
            {'username': 'entrep301_student5', 'full_name': 'Richard Branson', 'roll_number': '2023-ENT-0005'},
        ]
        
        for s_data in sample_students:
            student = User.query.filter_by(username=s_data['username']).first()
            if not student:
                student = User(
                    username=s_data['username'],
                    email=f"{s_data['username']}@student.university.edu",
                    full_name=s_data['full_name'],
                    role='student',
                    department='Entrepreneurship',
                    roll_number=s_data['roll_number'],
                    program='Bachelor of Science in Entrepreneurship',
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
        
        # NO PROGRAM HEAD CREATED FOR ENTREPRENEURSHIP
        
        print("\n" + "=" * 60)
        print("ENTREP 301 SECTION INITIALIZED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\nSection: {section.name}")
        print(f"Program: {section.program}")
        print(f"Year Level: {section.year_level}")
        print(f"Semester: {section.semester}")
        print(f"School Year: {section.school_year}")
        print(f"Total Class Assignments: {ClassAssignment.query.filter_by(section_id=section.id).count()}")
        print(f"Total Students Enrolled: {Enrollment.query.filter_by(section_id=section.id).count()}")
        
        print("\n" + "-" * 40)
        print("CLASS ASSIGNMENTS FOR ENTREP 301:")
        print("-" * 40)
        classes = ClassAssignment.query.filter_by(section_id=section.id, is_active=True).all()
        for ca in classes:
            print(f"  {ca.subject_name}")
            print(f"    Teacher: {ca.teacher.name}")
            print(f"    Department: {ca.teacher.department}")
            print(f"    Schedule ID: {ca.schedule_id}")
            print(f"    Type: {ca.subject_type}")
            print()
        
        print("\n" + "=" * 60)
        print("STUDENT LOGINS:")
        print("=" * 60)
        for s_data in sample_students:
            print(f"  Username: {s_data['username']}, Password: password123")
        
        print("\n" + "=" * 60)
        print("OTHER LOGINS:")
        print("=" * 60)
        print("  Admin:        admin / admin123")
        print("  Dean:         dean / password123")
        print("  Program Head:  ph_cs / password123 (Computer Science only)")
        
        print("\n" + "=" * 60)
        print("NOTE: No Program Head was created for Entrepreneurship.")
        print("Only ph_cs (Computer Science) exists as Program Head.")
        print("=" * 60)

if __name__ == '__main__':
    init_entrep301()