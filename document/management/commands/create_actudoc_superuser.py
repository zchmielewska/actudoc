from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from account.models import Profile
from document.models import Company


class Command(BaseCommand):
    help = "Create superuser with profile"

    def add_arguments(self, parser):
        parser.add_argument("company_code", type=str)
        parser.add_argument("password", type=str)

    def handle(self, *args, **options):
        company = Company.objects.create(
            name="admin",
            full_name="admin",
            code=options["company_code"],
        )

        user = User.objects.create(
            username="admin",
            email="example@example.com",
            is_staff=True,
            is_superuser=True,
        )
        user.set_password(options["password"])
        user.save()

        Profile.objects.create(
            user=user,
            company=company,
            role="admin",
            employee_num=1,
        )
