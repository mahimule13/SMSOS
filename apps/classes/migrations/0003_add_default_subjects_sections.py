from django.db import migrations


def create_default_subjects_and_sections(apps, schema_editor):
    ClassModel = apps.get_model('classes', 'ClassModel')
    Subject = apps.get_model('classes', 'Subject')
    Section = apps.get_model('classes', 'Section')

    default_subjects = [
        ('Science', 'SCI'),
        ('Social', 'SOC'),
        ('Mathematics', 'MTH'),
        ('English', 'ENG'),
    ]

    for name, code in default_subjects:
        Subject.objects.get_or_create(code=code, defaults={'name': name, 'is_active': True})

    for cls in ClassModel.objects.all():
        for sec in ['A', 'B', 'C']:
            Section.objects.get_or_create(class_model=cls, name=sec, defaults={'capacity': 50, 'is_active': True})


def reverse_func(apps, schema_editor):
    # Do not delete data on reverse to avoid accidental data loss
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0002_classmodel_class_incharge'),
    ]

    operations = [
        migrations.RunPython(create_default_subjects_and_sections, reverse_func),
    ]
