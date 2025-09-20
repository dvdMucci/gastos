# Generated manually to remove duplicates before applying unique constraint

from django.db import migrations

def remove_duplicates(apps, schema_editor):
    MonthlyForecast = apps.get_model('forecasts', 'MonthlyForecast')
    # Group by user and month, keep the first one
    seen = set()
    duplicates = []
    for forecast in MonthlyForecast.objects.all().order_by('user', 'month', 'id'):
        key = (forecast.user_id, forecast.month)
        if key in seen:
            duplicates.append(forecast.id)
        else:
            seen.add(key)
    # Delete duplicates
    MonthlyForecast.objects.filter(id__in=duplicates).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('forecasts', '0005_alter_monthlyforecast_options_and_more'),
    ]

    operations = [
        migrations.RunPython(remove_duplicates),
    ]