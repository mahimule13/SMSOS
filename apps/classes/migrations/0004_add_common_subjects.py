from django.db import migrations


def create_common_subjects(apps, schema_editor):
    Subject = apps.get_model('classes', 'Subject')

    subjects = [
        ('Mathematics', 'MTH'),
        ('English', 'ENG'),
        ('Physics', 'PHY'),
        ('Chemistry', 'CHM'),
        ('Biology', 'BIO'),
        ('Computer Science', 'CSC'),
        ('Information Technology', 'ICT'),
        ('History', 'HIS'),
        ('Geography', 'GEO'),
        ('Civics', 'CIV'),
        ('Economics', 'ECO'),
        ('Business Studies', 'BUS'),
        ('Accountancy', 'ACC'),
        ('Physical Education', 'PE'),
        ('Art', 'ART'),
        ('Music', 'MUS'),
        ('Environmental Science', 'ENV'),
        ('Hindi', 'HIN'),
        ('French', 'FR'),
        ('Sanskrit', 'SAN'),
        ('Psychology', 'PSY'),
        ('Sociology', 'SOC'),
    ]

    for name, code in subjects:
        Subject.objects.get_or_create(code=code, defaults={'name': name, 'is_active': True})


def reverse_func(apps, schema_editor):
    # Avoid deleting subjects on reverse to prevent data loss
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0003_add_default_subjects_sections'),
    ]

    operations = [
        migrations.RunPython(create_common_subjects, reverse_func),
    ]
