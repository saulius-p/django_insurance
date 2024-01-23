from django.db import models
import uuid
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from PIL import Image

########################################################################################################################
# POLICYHOLDER TABLE
########################################################################################################################


class Policyholder(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, default=1)
    personal_code = models.CharField("Personal code", primary_key=True, max_length=11, unique=True)
    # name = models.CharField("Name", max_length=20)
    # surname = models.CharField("Surname", max_length=20)
    birth_date = models.CharField("Birth date", max_length=10)  # Perteklinis. Reikėtų išskaičiuoti.
    tel_num = models.CharField("Tel. No.", max_length=14, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}. Birth date: {self.birth_date}."

########################################################################################################################
# CAR TABLE
########################################################################################################################


class Car(models.Model):
    plate_number = models.CharField(max_length=10, unique=True)
    make = models.CharField(max_length=30)
    model = models.CharField(max_length=30)
    body = models.CharField(max_length=10, null=True)
    mass = models.IntegerField(null=True)
    engine_displacement = models.IntegerField(null=True)
    power = models.IntegerField()  # kw
    fuel = models.CharField(max_length=8, null=True)
    manufacture_year = models.IntegerField(null=True)
    owner_personal_code = models.CharField(max_length=11)

    def __str__(self):
        return f"{self.plate_number} - {self.make} {self.model}"

########################################################################################################################
# POLICY TABLE
########################################################################################################################


class Policy(models.Model):
    policyholder = models.ForeignKey('Policyholder', related_name='policies', on_delete=models.SET_NULL, null=True,
                                     blank=True)
    policy_number = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text="Unique policy number.")
    start_date = models.DateField()
    end_date = models.DateField()
    policy_duration = models.IntegerField(default=365)
    policy_type = models.CharField(max_length=255)
    insurance_premium = models.FloatField()

    @property
    def start_month(self):
        return self.start_date.strftime("%Y.%m")

    def __str__(self):
        return f"{self.policy_number} {self.policyholder} {self.policy_type}. Duration: {self.policy_duration}. Start month: {self.start_month}"

########################################################################################################################


class MTPLData(models.Model):
    policy = models.OneToOneField('Policy', on_delete=models.CASCADE)
    driver_experience = models.IntegerField(default=10)
    car = models.ForeignKey('Car', related_name='mtpl_policies', on_delete=models.CASCADE, default=1)

    def __str__(self):
        return f"Policy number: {self.policy.policy_number}. Policy start: {self.policy.start_date}. \
                Experience: {self.driver_experience}. Make: {self.car.make}."


class CASCOData(models.Model):
    policy = models.OneToOneField('Policy', on_delete=models.CASCADE)
    driver_experience = models.IntegerField(default=10)
    car_alarm = models.BooleanField(default=False)
    car = models.ForeignKey('Car', related_name='casco_policies', on_delete=models.CASCADE, default=1)


class Risk(models.Model):
    property_risk = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f'{self.property_risk}'


class PropertyData(models.Model):
    policy = models.OneToOneField('Policy', on_delete=models.CASCADE)
    building_purpose = models.CharField(max_length=255, default="dwelling house")
    construction = models.CharField(max_length=255, default="brick/concrete")
    risks = models.ManyToManyField('Risk', help_text="Choose risks", related_name='property_policies')

    def __str__(self):
        return f"Policy number: {self.policy.policy_number}. Policy start: {self.policy.start_date}. \
                Building purpose: {self.building_purpose}. Construction: {self.construction}."


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    picture = models.ImageField(default='profile_pics/default.png', upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} profilis'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.picture.path)
        if img.height > 200 or img.width > 200:
            new_size = (200, 200)
            img.thumbnail(new_size)
            img.save(self.picture.path)

########################################################################################################################
# CLAIM TABLE
########################################################################################################################


class Claim(models.Model):
    incident_date = models.DateField()
    description_of_the_incident = models.CharField(max_length=1000)
    # supporting_documents = models.CharField(max_length=500, null=True, blank=True)
    policy = models.ForeignKey(Policy, related_name='claims', on_delete=models.SET_NULL, null=True)


########################################################################################################################
