from django.db import migrations

from domain.constants import DEFAULT_COURSE_CHECKPOINTS, DEFAULT_COURSE_NAME, TEAM_NAMES, ResultStatus


def seed_course(apps, schema_editor):
    Course = apps.get_model("domain", "Course")
    Checkpoint = apps.get_model("domain", "Checkpoint")
    TeamResult = apps.get_model("domain", "TeamResult")

    course, created = Course.objects.get_or_create(name=DEFAULT_COURSE_NAME, defaults={"is_active": True})
    if not created:
        return

    checkpoints = [
        Checkpoint(course=course, code=code, name=f"打卡点 {code}", position=position)
        for position, code in enumerate(DEFAULT_COURSE_CHECKPOINTS, start=1)
    ]
    Checkpoint.objects.bulk_create(checkpoints)

    TeamResult.objects.bulk_create(
        [TeamResult(team_name=name, course=course, status=ResultStatus.PENDING) for name in TEAM_NAMES]
    )


def remove_course(apps, schema_editor):
    Course = apps.get_model("domain", "Course")
    Course.objects.filter(name=DEFAULT_COURSE_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("domain", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_course, remove_course),
    ]
