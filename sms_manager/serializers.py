from .models import UserOTP
from rest_framework import serializers


class UserOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserOTP
        fields = "__all__"
