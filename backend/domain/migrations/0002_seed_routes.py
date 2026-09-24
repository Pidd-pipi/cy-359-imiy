from django.db import migrations


def seed_routes(apps, schema_editor):
    Route = apps.get_model("domain", "Route")
    routes = [
        {
            "name": "城市经典线",
            "description": "成人组标准线路，共 6 个打卡点",
            "checkpoint_sequence": ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"],
        },
        {
            "name": "公园亲子线",
            "description": "亲子组体验线路，共 4 个打卡点",
            "checkpoint_sequence": ["CP1", "CP2", "CP3", "CP4"],
        },
    ]
    for item in routes:
        Route.objects.create(**item)


def remove_routes(apps, schema_editor):
    Route = apps.get_model("domain", "Route")
    Route.objects.filter(name__in=["城市经典线", "公园亲子线"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("domain", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_routes, remove_routes),
    ]
