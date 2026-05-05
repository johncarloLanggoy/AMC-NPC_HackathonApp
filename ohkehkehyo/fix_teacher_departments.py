# fix_teacher_departments.py
from app import app
from models import db, Teacher

def fix_teacher_departments():
    with app.app_context():
        print("=" * 60)
        print("UPDATING TEACHER DEPARTMENTS")
        print("=" * 60)
        
        # Map teachers to correct departments
        teacher_department_map = {
            # CCS/Computer Science Teachers
            'Cacho Romark': 'Computer Science',
            'Christian Esguerra': 'Computer Science',
            'Mark Gabriel Antipala': 'Computer Science',
            'Rhavee Valencia': 'Computer Science',
            'Dong Rodrigo': 'Computer Science',
            
            # Entrepreneurship Teachers
            'Evelyn Tanangonan': 'Entrepreneurship',
            'Joseph Briola': 'Entrepreneurship',
            'Shiela SanJuan': 'Entrepreneurship', 
            'Teodoro Canay': 'Entrepreneurship',
            'David Ryan Tolentino': 'Entrepreneurship',
            'Jay R Loreto': 'Entrepreneurship',
            
            # Financial Management Teachers
            'Mario Camacho': 'Financial Management',
            'Neil Bibal': 'Financial Management',
            'Mariel Prado': 'Financial Management',
            'Jabez Espiritu': 'Financial Management',
            'Leandro Tulod': 'Financial Management',
            
            # Other teachers
            'Evelyn Tanganoan': 'Entrepreneurship',
            'Daisy Cuadra': 'Arts and Humanities',
            'Mary Shane Carpila': 'Social Sciences',
            'Vevencio Gabuya Jr.': 'Physical Education'
        }
        
        updated_count = 0
        for teacher_name, department in teacher_department_map.items():
            teacher = Teacher.query.filter_by(name=teacher_name).first()
            if teacher:
                if teacher.department != department:
                    old_dept = teacher.department
                    teacher.department = department
                    updated_count += 1
                    print(f"  ✓ {teacher_name}: {old_dept} → {department}")
            else:
                print(f"  ✗ Teacher not found: {teacher_name}")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ Updated {updated_count} teachers")
        print("=" * 60)
        
        # Show teacher counts by department
        print("\n📊 TEACHER COUNTS BY DEPARTMENT:")
        print("-" * 40)
        departments = db.session.query(Teacher.department, db.func.count(Teacher.id)).filter_by(is_active=True).group_by(Teacher.department).all()
        for dept, count in departments:
            print(f"  {dept:25} → {count} teachers")

if __name__ == '__main__':
    fix_teacher_departments()