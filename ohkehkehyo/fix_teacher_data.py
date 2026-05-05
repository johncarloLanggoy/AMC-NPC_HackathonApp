# fix_teacher_data.py
from app import app
from models import db, User, Teacher, Evaluation, ClassEvaluation, ClassAssignment
import random
from datetime import datetime, timedelta

def fix_teacher_data():
    with app.app_context():
        print("=" * 60)
        print("FIXING TEACHER DASHBOARD DATA")
        print("=" * 60)
        
        # Get the teacher
        teacher = Teacher.query.filter_by(name='Cacho Romark').first()
        if not teacher:
            print("Teacher 'Cacho Romark' not found!")
            return
        
        print(f"Found teacher: {teacher.name} (ID: {teacher.id})")
        
        # Get all students
        students = User.query.filter_by(role='student', is_active=True).all()
        print(f"Found {len(students)} students")
        
        # Get program head and dean users
        program_head = User.query.filter_by(role='program_head').first()
        dean = User.query.filter_by(role='dean').first()
        
        print(f"Program head: {program_head.username if program_head else 'Not found'}")
        print(f"Dean: {dean.username if dean else 'Not found'}")
        
        evaluation_count = 0
        
        # ============================================
        # 1. CREATE OLD-STYLE EVALUATIONS (for teacher dashboard)
        # ============================================
        print("\n📝 Creating old-style evaluations...")
        
        # Student evaluations (50% weight)
        for student in students[:10]:  # Use first 10 students
            existing = Evaluation.query.filter_by(
                teacher_id=teacher.id,
                evaluator_id=student.id,
                evaluator_role='student'
            ).first()
            
            if not existing:
                # Generate random scores (3-5 range for good teacher)
                teaching_clarity = random.randint(3, 5)
                engagement = random.randint(3, 5)
                fairness = random.randint(3, 5)
                
                avg_score = (teaching_clarity + engagement + fairness) / 3
                
                evaluation = Evaluation(
                    teacher_id=teacher.id,
                    evaluator_id=student.id,
                    evaluator_role='student',
                    teaching_clarity=teaching_clarity,
                    engagement=engagement,
                    fairness=fairness,
                    comments=f"Student evaluation: Teaching clarity {teaching_clarity}/5, Engagement {engagement}/5, Fairness {fairness}/5",
                    is_anonymous=True,
                    submitted_at=datetime.now() - timedelta(days=random.randint(0, 30))
                )
                db.session.add(evaluation)
                evaluation_count += 1
                print(f"  ✓ Added student evaluation from {student.full_name} (Score: {avg_score:.1f}/5)")
        
        # Program head evaluations (30% weight)
        if program_head:
            existing_ph = Evaluation.query.filter_by(
                teacher_id=teacher.id,
                evaluator_id=program_head.id,
                evaluator_role='program_head'
            ).first()
            
            if not existing_ph:
                curriculum = random.randint(3, 5)
                assessment = random.randint(3, 5)
                mentoring = random.randint(3, 5)
                
                avg_score = (curriculum + assessment + mentoring) / 3
                
                evaluation = Evaluation(
                    teacher_id=teacher.id,
                    evaluator_id=program_head.id,
                    evaluator_role='program_head',
                    curriculum_implementation=curriculum,
                    assessment_quality=assessment,
                    mentoring=mentoring,
                    comments=f"Program head evaluation: Curriculum {curriculum}/5, Assessment {assessment}/5, Mentoring {mentoring}/5",
                    submitted_at=datetime.now() - timedelta(days=random.randint(0, 15))
                )
                db.session.add(evaluation)
                evaluation_count += 1
                print(f"  ✓ Added program head evaluation (Score: {avg_score:.1f}/5)")
        
        # Dean evaluations (20% weight)
        if dean:
            existing_dean = Evaluation.query.filter_by(
                teacher_id=teacher.id,
                evaluator_id=dean.id,
                evaluator_role='dean'
            ).first()
            
            if not existing_dean:
                attendance = random.randint(3, 5)
                commitment = random.randint(3, 5)
                teaching_quality = random.randint(3, 5)
                
                avg_score = (attendance + commitment + teaching_quality) / 3
                
                evaluation = Evaluation(
                    teacher_id=teacher.id,
                    evaluator_id=dean.id,
                    evaluator_role='dean',
                    attendance=attendance,
                    commitment=commitment,
                    teaching_quality=teaching_quality,
                    comments=f"Dean evaluation: Attendance {attendance}/5, Commitment {commitment}/5, Teaching Quality {teaching_quality}/5",
                    submitted_at=datetime.now() - timedelta(days=random.randint(0, 10))
                )
                db.session.add(evaluation)
                evaluation_count += 1
                print(f"  ✓ Added dean evaluation (Score: {avg_score:.1f}/5)")
        
        # ============================================
        # 2. ALSO CREATE CLASS EVALUATIONS (for student dashboard)
        # ============================================
        print("\n📝 Creating class evaluations...")
        
        # Get class assignments for this teacher
        class_assignments = ClassAssignment.query.filter_by(teacher_id=teacher.id, is_active=True).all()
        print(f"Found {len(class_assignments)} class assignments for this teacher")
        
        for class_assign in class_assignments:
            for student in students[:8]:
                existing_class = ClassEvaluation.query.filter_by(
                    class_assignment_id=class_assign.id,
                    evaluator_id=student.id
                ).first()
                
                if not existing_class:
                    evaluation = ClassEvaluation(
                        class_assignment_id=class_assign.id,
                        evaluator_id=student.id,
                        teaching_clarity=random.randint(3, 5),
                        engagement=random.randint(3, 5),
                        fairness=random.randint(3, 5),
                        subject_mastery=random.randint(3, 5),
                        punctuality=random.randint(3, 5),
                        comments=f"Good class! Enjoyed {class_assign.subject_name}",
                        is_anonymous=True,
                        submitted_at=datetime.now() - timedelta(days=random.randint(0, 30))
                    )
                    db.session.add(evaluation)
                    evaluation_count += 1
                    print(f"  ✓ Added class evaluation for {class_assign.subject_name} from {student.full_name}")
        
        # Commit all changes
        db.session.commit()
        
        print("\n" + "=" * 60)
        print(f"✓ Successfully created {evaluation_count} total evaluations!")
        print("=" * 60)
        
        # Show summary
        print("\n📊 OLD-STYLE EVALUATIONS SUMMARY:")
        student_count = Evaluation.query.filter_by(teacher_id=teacher.id, evaluator_role='student').count()
        ph_count = Evaluation.query.filter_by(teacher_id=teacher.id, evaluator_role='program_head').count()
        dean_count = Evaluation.query.filter_by(teacher_id=teacher.id, evaluator_role='dean').count()
        
        print(f"  - Student evaluations: {student_count}")
        print(f"  - Program head evaluations: {ph_count}")
        print(f"  - Dean evaluations: {dean_count}")
        print(f"  - Total old-style: {student_count + ph_count + dean_count}")
        
        print("\n📊 NEW-STYLE CLASS EVALUATIONS SUMMARY:")
        class_count = ClassEvaluation.query.filter(
            ClassEvaluation.class_assignment_id.in_([c.id for c in class_assignments])
        ).count()
        print(f"  - Class evaluations: {class_count}")
        
        print("\n" + "=" * 60)
        print("✅ Now refresh your browser to see the teacher dashboard with data!")
        print("=" * 60)
        
        # Calculate and display final score
        print("\n📈 EXPECTED SCORES FOR TEACHER:")
        
        # Calculate averages
        student_evals = Evaluation.query.filter_by(teacher_id=teacher.id, evaluator_role='student').all()
        if student_evals:
            student_avg = sum(e.calculate_raw_score() for e in student_evals) / len(student_evals)
            print(f"  Student Average: {student_avg:.2f}/5 (Weight: 50%) → {student_avg * 0.5:.2f}")
        
        ph_evals = Evaluation.query.filter_by(teacher_id=teacher.id, evaluator_role='program_head').all()
        if ph_evals:
            ph_avg = sum(e.calculate_raw_score() for e in ph_evals) / len(ph_evals)
            print(f"  Program Head Average: {ph_avg:.2f}/5 (Weight: 30%) → {ph_avg * 0.3:.2f}")
        
        dean_evals = Evaluation.query.filter_by(teacher_id=teacher.id, evaluator_role='dean').all()
        if dean_evals:
            dean_avg = sum(e.calculate_raw_score() for e in dean_evals) / len(dean_evals)
            print(f"  Dean Average: {dean_avg:.2f}/5 (Weight: 20%) → {dean_avg * 0.2:.2f}")

if __name__ == '__main__':
    fix_teacher_data()