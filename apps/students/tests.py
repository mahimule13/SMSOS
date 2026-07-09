from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.classes.models import ClassModel, Section, Subject, SubjectAllocation
from apps.students.models import Student
from apps.teachers.models import Teacher


class AttendanceViewTests(TestCase):
    def test_teacher_attendance_view_renders_without_error(self):
        user = User.objects.create_user(username='teacher1', password='secret123')
        UserProfile.objects.create(user=user, role='teacher')

        teacher = Teacher.objects.create(
            user=user,
            employee_id='T-001',
            phone='1234567890',
            address='Test address',
            gender='M',
            blood_group='O+',
            dob='1990-01-01',
            photo=SimpleUploadedFile('teacher.png', b'fake-image', content_type='image/png'),
            aadhar='123456789012',
            pan='ABCDE1234F',
            qualification='MSc',
            experience_years=3,
            joining_date='2020-01-01',
            base_salary=10000,
        )

        class_model = ClassModel.objects.create(name='Class 10', standard=10)
        section = Section.objects.create(class_model=class_model, name='A')
        subject = Subject.objects.create(name='Math', code='MATH001')
        SubjectAllocation.objects.create(section=section, subject=subject, teacher=teacher)

        student_user = User.objects.create_user(username='student1', password='secret123')
        UserProfile.objects.create(user=student_user, role='student')
        Student.objects.create(
            user=student_user,
            student_id='S-001',
            admission_number='ADM001',
            roll_number='1',
            dob='2010-01-01',
            gender='M',
            blood_group='O+',
            address='Student address',
            phone='9876543210',
            email='student@example.com',
            photo=SimpleUploadedFile('student.png', b'fake-image', content_type='image/png'),
            section=section,
            father_name='Father',
            father_phone='1111111111',
            mother_name='Mother',
            mother_phone='2222222222',
            guardian_name='Guardian',
            guardian_phone='3333333333',
            admission_date='2023-01-01',
        )

        self.client.force_login(user)
        response = self.client.get(reverse('students:attendance'))

        self.assertEqual(response.status_code, 200)
