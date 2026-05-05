# add_programs.py
from app import app
from models import db, Program, User

def add_all_programs():
    with app.app_context():
        print("=" * 60)
        print("ADDING PROGRAMS FOR ALL DEPARTMENTS")
        print("=" * 60)
        
        # Get all program heads
        program_heads = {
            ph.department: ph.id for ph in User.query.filter_by(role='program_head').all()
        }
        
        # Define programs to add
        programs_data = [
            {
                'name': 'Bachelor of Science in Computer Science',
                'department': 'Computer Science',
                'coordinator_username': 'ph_ccs'
            },
            {
                'name': 'Bachelor of Science in Information Technology',
                'department': 'Computer Science',
                'coordinator_username': 'ph_ccs'
            },
            {
                'name': 'Bachelor of Science in Entrepreneurship',
                'department': 'Entrepreneurship',
                'coordinator_username': 'ph_entrep'
            },
            {
                'name': 'Bachelor of Science in Financial Management',
                'department': 'Financial Management',
                'coordinator_username': 'ph_fm'
            },
            {
                'name': 'Bachelor of Science in Business Administration',
                'department': 'Financial Management',
                'coordinator_username': 'ph_fm'
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for prog_data in programs_data:
            # Find coordinator by username
            coordinator = User.query.filter_by(username=prog_data['coordinator_username']).first()
            coordinator_id = coordinator.id if coordinator else None
            
            # Check if program already exists
            existing = Program.query.filter_by(name=prog_data['name']).first()
            
            if existing:
                # Update existing program
                existing.department = prog_data['department']
                if coordinator_id:
                    existing.coordinator_id = coordinator_id
                updated_count += 1
                print(f"✓ Updated program: {prog_data['name']}")
            else:
                # Create new program
                new_program = Program(
                    name=prog_data['name'],
                    department=prog_data['department'],
                    coordinator_id=coordinator_id
                )
                db.session.add(new_program)
                created_count += 1
                print(f"✓ Created program: {prog_data['name']}")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ Created {created_count} programs, Updated {updated_count} programs")
        print("=" * 60)
        
        # Show all programs
        print("\n📋 ALL PROGRAMS IN SYSTEM:")
        print("-" * 50)
        for program in Program.query.all():
            coordinator_name = program.coordinator.full_name if program.coordinator else "Not assigned"
            teacher_count = len(program.teachers)
            print(f"  {program.name[:35]:35} → {program.department:20} → Head: {coordinator_name[:20]} → {teacher_count} teachers")

if __name__ == '__main__':
    add_all_programs()