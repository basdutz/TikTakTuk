from django.db import models

class UserAccount(models.Model):
    user_id = models.UUIDField(primary_key=True)
    username = models.CharField(max_length=100)
    password = models.CharField(db_column="PASSWORD", max_length=255)

    class Meta:
        db_table = '"tiktaktuk"."USER_ACCOUNT"'
        managed = False


class Customer(models.Model):
    customer_id = models.UUIDField(primary_key=True)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    user = models.OneToOneField(
        UserAccount,
        on_delete=models.CASCADE,
        db_column="user_id"
    )

    class Meta:
        db_table = '"tiktaktuk"."CUSTOMER"'
        managed = False


class Organizer(models.Model):
    organizer_id = models.UUIDField(primary_key=True)
    organization_name = models.CharField(max_length=100)
    contact_email = models.CharField(max_length=100, null=True, blank=True)
    user = models.OneToOneField(
        UserAccount,
        on_delete=models.CASCADE,
        db_column="user_id"
    )

    class Meta:
        db_table = '"tiktaktuk"."ORGANIZER"'
        managed = False