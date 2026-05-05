# fix_program_head_data.py
from app import app
from models import db, User, Teacher, Evaluation, ClassAssignment
import random
from datetime import datetime, timedelta

def fix_program_head_data():
    with app.app_context():
        print("=" * 60)
        print("FIXING PROGRAM HEAD DASHBOARD")
        print("=" * 60)
        
        # Get program head
        program_head = User.query.filter_by(role='program_head').first()
        if not program_head:
            print("No program head found! Creating one...")
            program_head = User(
                username='ph_cs',
                email='ph.cs@university.edu',
                full_name='Dr. James Wilson',
                role='program_head',
                department='Computer Science',
                is_active=True
            )
            program_head.set_password('password123')
            db.session.add(program_head)
            db.session.commit()
            print(f"Created program head: {program_head.username}")
        
        print(f"Program Head: {program_head.full_name}")
        print(f"Department: {program_head.department}")
        
        # Create teachers in Computer Science department if none exist
        cs_teachers = Teacher.query.filter_by(department='Computer Science').all()
        
        if not cs_teachers:
            print("\n📝 Creating Computer Science teachers...")
            teachers_data = [
                {'name': 'Cacho Romark', 'email': 'romark.cacho@university.edu', 'subjects': 'Advance Mobile Computing, Web Development'},
                {'name': 'Christian Esguerra', 'email': 'christian.esguerra@university.edu', 'subjects': 'Computer Architecture, Operating Systems'},
                {'name': 'Mark Gabriel Antipala', 'email': 'mark.antipala@university.edu', 'subjects': 'Web Systems, Database Management'},
                {'name': 'Rhavee Valencia', 'email': 'rhavee.valencia@university.edu', 'subjects': 'Information Assurance, Network Security'},
                {'name': 'Dong Rodrigo', 'email': 'dong.rodrigo@university.edu', 'subjects': 'Capstone Project, Research Methods'},
            ]
            
            for t_data in teachers_data:
                teacher = Teacher(
                    name=t_data['name'],
                    email=t_data['email'],
                    department='Computer Science',
                    subjects=t_data['subjects'],
                    is_active=True
                )
                db.session.add(teacher)
                print(f"  ✓ Created teacher: {teacher.name}")
            
            db.session.commit()
            cs_teachers = Teacher.query.filter_by(department='Computer Science').all()
        
        print(f"\nFound {len(cs_teachers)} teachers in Computer Science department:")
        for teacher in cs_teachers:
            print(f"  - {teacher.name}")
        
        # Get students for evaluations
        students = User.query.filter_by(role='student', is_active=True).all()
        
        # Create program head evaluations for each teacher
        print("\n📝 Creating program head evaluations...")
        evaluation_count = 0
        
        for teacher in cs_teachers:
            # Check if program head already evaluated this teacher
            existing = Evaluation.query.filter_by(
                teacher_id=teacher.id,
                evaluator_id=program_head.id,
                evaluator_role='program_head'
            ).first()
            
            if not existing:
                # Generate scores (4-5 range for good teachers)
                curriculum = random.randint(4, 5)
                assessment = random.randint(4, 5)
                mentoring = random.randint(4, 5)
                
                evaluation = Evaluation(
                    teacher_id=teacher.id,
                    evaluator_id=program_head.id,
                    evaluator_role='program_head',
                    curriculum_implementation=curriculum,
                    assessment_quality=assessment,
                    mentoring=mentoring,
                    comments=f"Good performance. Curriculum implementation: {curriculum}/5, Assessment: {assessment}/5, Mentoring: {mentoring}/5",
                    submitted_at=datetime.now() - timedelta(days=random.randint(0, 30))
                )
                db.session.add(evaluation)
                evaluation_count += 1
                print(f"  ✓ Program head evaluated {teacher.name}")
        
        # Also create student evaluations for these teachers
        print("\n📝 Creating student evaluations...")
        student_eval_count = 0
        
        for teacher in cs_teachers:
            for student in students[:8]:  # First 8 students
                existing_student = Evaluation.query.filter_by(
                    teacher_id=teacher.id,
                    evaluator_id=student.id,
                    evaluator_role='student'
                ).first()
                
                if not existing_student and len(students) > 0:
                    evaluation = Evaluation(
                        teacher_id=teacher.id,
                        evaluator_id=student.id,
                        evaluator_role='student',
                        teaching_clarity=random.randint(3, 5),
                        engagement=random.randint(3, 5),
                        fairness=random.randint(3, 5),
                        comments=f"Good teacher!",
                        is_anonymous=True,
                        submitted_at=datetime.now() - timedelta(days=random.randint(0, 30))
                    )
                    db.session.add(evaluation)
                    student_eval_count += 1
        
        db.session.commit()
        
        print(f"\n✓ Created {evaluation_count} program head evaluations")
        print(f"✓ Created {student_eval_count} student evaluations")
        
        # Also update program assignments
        print("\n📝 Updating program assignments...")
        
        # Create a program if it doesn't exist
        cs_program = None
        for prog in program_head.programs_managed:
            cs_program = prog
        
        if not cs_program:
            from models import Program
            cs_program = Program(
                name='Bachelor of Science in Computer Science',
                department='Computer Science',
                coordinator_id=program_head.id
            )
            db.session.add(cs_program)
            db.session.commit()
            print(f"  ✓ Created Computer Science program")
        
        # Add teachers to program
        for teacher in cs_teachers:
            if teacher not in cs_program.teachers:
                cs_program.teachers.append(teacher)
                print(f"  ✓ Added {teacher.name} to {cs_program.name}")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("PROGRAM HEAD DASHBOARD SUMMARY")
        print("=" * 60)
        
        # Calculate statistics
        teachers_in_dept = Teacher.query.filter_by(department='Computer Science', is_active=True).count()
        print(f"\nTeachers in Computer Science: {teachers_in_dept}")
        
        # Count pending evaluations (teachers not evaluated by program head)
        evaluated_ids = db.session.query(Evaluation.teacher_id).filter_by(
            evaluator_id=program_head.id,
            evaluator_role='program_head'
        ).distinct().all()
        evaluated_ids = [e[0] for e in evaluated_ids]
        
        pending = Teacher.query.filter(
            Teacher.department == 'Computer Science',
            Teacher.is_active == True,
            Teacher.id.notin_(evaluated_ids)
        ).count()
        
        print(f"Pending evaluations: {pending}")
        
        # Calculate department average
        all_evaluations = Evaluation.query.filter(
            Evaluation.teacher_id.in_([t.id for t in cs_teachers])
        ).all()
        
        if all_evaluations:
            total_score = sum(e.calculate_weighted_score() for e in all_evaluations)
            avg_score = total_score / len(all_evaluations)
            print(f"Department Average Score: {avg_score:.2f}/5")
        else:
            print("Department Average Score: 0.00/5")
        
        print(f"Total Evaluations: {len(all_evaluations)}")
        
        print("\n" + "=" * 60)
        print("✅ Now refresh your Program Head dashboard!")
        print(f"   Login with: {program_head.username} / password123")
        print("=" * 60)

if __name__ == '__main__':
    fix_program_head_data()