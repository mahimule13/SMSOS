from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_remove_userprofile_schoolname'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='school_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
