from django.db import models

# Create your models here.
class UserOTP(models.Model):
    phone_number = models.CharField(max_length=15)
    otp_secret = models.CharField(max_length=100)
    otp_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_otp'
        verbose_name = 'User OTP'
        verbose_name_plural = 'User OTPs'


    def __str__(self):
        return f"OTP for {self.phone_number} is {self.otp_secret}"