from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

from document.models import Company


# Changes to the built-in User model
User._meta.get_field('email')._unique = True
User._meta.get_field('email').blank = False
User._meta.get_field('email').null = False
User._meta.get_field('first_name').blank = False
User._meta.get_field('first_name').null = False
User._meta.get_field('last_name').blank = False
User._meta.get_field('last_name').null = False


def get_name(self):
    return f"{self.first_name} {self.last_name}"


User.add_to_class("__str__", get_name)


class Profile(models.Model):
    ROLES = (
        ("admin", "admin"),
        ("contributor", "contributor"),
        ("viewer", "viewer")
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=11, choices=ROLES, default="viewer")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)
    employee_num = models.PositiveIntegerField()

    class Meta:
        indexes = [models.Index(fields=["user", ])]
        unique_together = ("company", "employee_num")
