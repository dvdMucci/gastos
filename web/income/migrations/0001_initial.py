# Generated manually for income app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IncomeCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('icon', models.CharField(default='fas fa-tag', max_length=50, verbose_name='Icon')),
                ('color', models.CharField(default='primary', max_length=20, verbose_name='Color')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
            ],
            options={
                'verbose_name': 'Income Category',
                'verbose_name_plural': 'Income Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='IncomeSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('icon', models.CharField(default='fas fa-dollar-sign', max_length=50, verbose_name='Icon')),
                ('color', models.CharField(default='success', max_length=20, verbose_name='Color')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
            ],
            options={
                'verbose_name': 'Income Source',
                'verbose_name_plural': 'Income Sources',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='IncomeType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('salary', 'SALARY'), ('bonus', 'BONUS'), ('freelance', 'FREELANCE'), ('investment', 'INVESTMENT'), ('gift', 'GIFT'), ('other', 'OTHER')], max_length=20, unique=True, verbose_name='Type')),
                ('icon', models.CharField(default='fas fa-money-bill-wave', max_length=50, verbose_name='Icon')),
            ],
            options={
                'verbose_name': 'Income Type',
                'verbose_name_plural': 'Income Types',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Income',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Date')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Amount')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('is_recurring', models.BooleanField(default=False, verbose_name='Is Recurring')),
                ('recurring_frequency', models.CharField(blank=True, choices=[('monthly', 'MONTHLY'), ('quarterly', 'QUARTERLY'), ('yearly', 'YEARLY')], max_length=20, null=True, verbose_name='Recurring Frequency')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='income.incomecategory', verbose_name='Category')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='income.incomesource', verbose_name='Source')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='income.incometype', verbose_name='Type')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.customuser', verbose_name='User')),
            ],
            options={
                'verbose_name': 'Income',
                'verbose_name_plural': 'Income',
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='income',
            index=models.Index(fields=['user', 'date'], name='income_income_user_id_123456_idx'),
        ),
        migrations.AddIndex(
            model_name='income',
            index=models.Index(fields=['user', 'is_recurring'], name='income_income_user_id_234567_idx'),
        ),
        migrations.AddIndex(
            model_name='income',
            index=models.Index(fields=['date'], name='income_income_date_idx'),
        ),
        migrations.AddIndex(
            model_name='income',
            index=models.Index(fields=['category'], name='income_income_category_idx'),
        ),
        migrations.AddIndex(
            model_name='income',
            index=models.Index(fields=['source'], name='income_income_source_idx'),
        ),
        migrations.AddIndex(
            model_name='income',
            index=models.Index(fields=['type'], name='income_income_type_idx'),
        ),
    ]