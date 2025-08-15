from rest_framework import serializers
from .models import (
    BookingMasterData,
    District,
    StockYard,
    Mandal,
    MandalVillage,
    BookingUserCredential,
)


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = "__all__"


class DistrictStockyardSerializer(serializers.ModelSerializer):
    district = DistrictSerializer()

    class Meta:
        model = StockYard
        fields = "__all__"


class MandalSerializer(serializers.ModelSerializer):
    district = DistrictSerializer()

    class Meta:
        model = Mandal
        fields = "__all__"


class MandalVillageSerializer(serializers.ModelSerializer):
    mandal = MandalSerializer()

    class Meta:
        model = MandalVillage
        fields = "__all__"


class BookingUserCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingUserCredential
        fields = "__all__"

class CreateBookingMasterDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingMasterData
        fields = "__all__"


class BookingMasterDataSerializer(serializers.ModelSerializer):
    district = DistrictSerializer()
    stockyard = DistrictStockyardSerializer()
    delivery_district = DistrictSerializer()
    delivery_mandal = MandalSerializer()
    delivery_village = MandalVillageSerializer()
    booking_user = BookingUserCredentialSerializer()

    class Meta:
        model = BookingMasterData
        fields = "__all__"
