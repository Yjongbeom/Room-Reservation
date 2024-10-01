from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, studentNumber, password=None, **extra_fields):
        if not studentNumber:
            raise ValueError('The Email field must be set')
        user = self.model(studentNumber=studentNumber, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, studentNumber, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(studentNumber, password, **extra_fields)

class Users(AbstractBaseUser, PermissionsMixin):
    studentNumber = models.CharField(max_length=150, unique=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    phone = models.CharField(max_length=255)
    refresh_token = models.TextField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'studentNumber'
    REQUIRED_FIELDS = ['name', 'phone']

# Create your models here.
class Reservation(models.Model):
    reservation_id = models.AutoField(primary_key=True)
    end_time = models.TimeField()
    reason = models.CharField(max_length=255)
    building = models.CharField(max_length=255)
    floor = models.IntegerField()
    year = models.IntegerField()
    month = models.IntegerField()
    day = models.IntegerField()
    start_time = models.TimeField()
    room = models.IntegerField()
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
