# fix_programs.py
from app import app
from models import db, User, Program, Teacher

def fix_programs():
    with app.app_context():
        print("Fixing program assignments...")
        
        # Get all program heads
        program_heads = User.query.filter_by(role='program_head').all()
        
        # Create a mapping of departments to program heads
        dept_to_head = {}
        for head in program_heads:
            if head.department:
                dept_to_head[head.department] = head.id
        
        # Update programs with coordinators
        programs = Program.query.all()
        for program in programs:
            # Assign coordinator if available for this department
            if program.department in dept_to_head:
                program.coordinator_id = dept_to_head[program.department]
                print(f"Assigned {program.department} program to {program.department} program head")
            
            # Find teachers in this department and add them to the program
            teachers = Teacher.query.filter_by(department=program.department).all()
            for teacher in teachers:
                if teacher not in program.teachers:
                    program.teachers.append(teacher)
                    print(f"Added {teacher.name} to {program.name}")
        
        db.session.commit()
        
        # Verify the fixes
        print("\n" + "="*50)
        print("FIXED PROGRAM ASSIGNMENTS:")
        print("="*50)
        for program in Program.query.all():
            coordinator = User.query.get(program.coordinator_id)
            coordinator_name = coordinator.full_name if coordinator else "Not assigned"
            teacher_count = len(program.teachers)
            print(f"{program.name}:")
            print(f"  - Coordinator: {coordinator_name}")
            print(f"  - Teachers: {teacher_count}")
            if teacher_count > 0:
                for teacher in program.teachers:
                    print(f"    * {teacher.name}")
            print()

if __name__ == '__main__':
    fix_programs()