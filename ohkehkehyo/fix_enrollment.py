# fix_enrollment.py
from app import app, db
from models import User, Section, Enrollment

with app.app_context():
    # Find the student
    student = User.query.filter_by(username='langgoy_john_carlo').first()
    
    if student:
        print(f"Found student: {student.username} - {student.full_name}")
        print(f"Current is_irregular: {student.is_irregular}")
        
        # Find the section
        section = Section.query.filter_by(name='BSIT 307').first()
        
        if section:
            print(f"Found section: {section.name}")
            
            # Check if already enrolled
            existing = Enrollment.query.filter_by(
                student_id=student.id,
                section_id=section.id
            ).first()
            
            if existing:
                print(f"Student already enrolled in {section.name}")
            else:
                # Create enrollment
                enrollment = Enrollment(
                    student_id=student.id,
                    section_id=section.id,
                    is_active=True
                )
                db.session.add(enrollment)
                db.session.commit()
                print(f"✓ Enrolled {student.full_name} in {section.name}")
        else:
            print("Section 'BSIT 307' not found!")
            print("Available sections:")
            for s in Section.query.all():
                print(f"  - {s.name}")
    else:
        print("Student not found!")
        print("Available students:")
        for s in User.query.filter_by(role='student').all():
            print(f"  - {s.username} ({s.full_name})")