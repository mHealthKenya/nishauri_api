from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from .manager import CustomUserManager
import uuid


class Facilities(models.Model):
    mfl_code = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=80)
    county = models.CharField(max_length=30)
    sub_county = models.CharField(max_length=80)

    class Meta:
        db_table = "Facilities"


class User(AbstractUser):
    username = models.CharField(null=True, blank=True, max_length=250)
    is_staff = None
    is_superuser = None
    first_name = models.CharField(null=True, blank=True, max_length=250)
    last_name = models.CharField(null=True, blank=True, max_length=250)
    msisdn = models.CharField(max_length=15, unique=True)
    CCCNo = models.CharField(max_length=15)
    securityQuestion = models.CharField(null=True, blank=True, max_length=150)
    securityAnswer = models.CharField(max_length=250, null=True)
    termsAccepted = models.BooleanField(default=0)
    initial_facility = models.CharField(max_length=50, default=0)
    current_facility = models.ForeignKey(Facilities, to_field='mfl_code', default=12345, db_column='current_facility', on_delete=models.CASCADE)
    language_preference = models.CharField(max_length=20, default='English')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    chat_number = models.CharField(blank=True, max_length=250)
    # jwt_secret = models.UUIDField(default=uuid.uuid4)

    REQUIRED_FIELDS = ['CCCNo', 'securityQuestion', 'securityAnswer', 'termsAccepted']
    USERNAME_FIELD = 'msisdn'

    objects = CustomUserManager()

    def __str__(self):
        return self.msisdn

    class Meta:
        db_table = "User"


class ChatTokens(models.Model):
    token = models.CharField(null=True, blank=True, max_length=550)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "ChatTokens"


class Dependants(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    CCCNo = models.CharField(max_length=15, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=60, blank=False)
    surname = models.CharField(max_length=60, null=True, blank=True)
    heiNumber = models.CharField(max_length=20, blank=False)
    dob = models.DateField(blank=True, null=True)
    approved = models.CharField(default='Pending', max_length=20)

    class Meta:
        db_table = "Dependants"


class Regiment(models.Model):
    Regiment = models.CharField(max_length=100)
    date_started = models.DateField(default="2020-05-05")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "Regiment History"


class PartnerFacility(models.Model):
    mfl_code = models.PositiveIntegerField()
    partner_id = models.PositiveIntegerField()

    class Meta:
        db_table = "PartnerFacility"

