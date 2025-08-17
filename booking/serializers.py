from rest_framework import serializers
from .models import (
    BookingMasterData,
    District,
    StockYard,
    Mandal,
    MandalVillage,
    BookingUserCredential,
    BookingHistory,
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
    delivery_district = serializers.IntegerField(write_only=True)
    delivery_mandal = serializers.IntegerField(write_only=True)
    delivery_village = serializers.IntegerField(write_only=True)
    district = serializers.IntegerField(write_only=True)
    stockyard = serializers.CharField(write_only=True)

    class Meta:
        model = BookingMasterData
        fields = "__all__"

    def validate_delivery_district(self, value):
        try:
            District.objects.get(did=value)
        except District.DoesNotExist:
            raise serializers.ValidationError(
                f"District with did {value} does not exist."
            )
        return value

    def validate_delivery_mandal(self, value):
        try:
            Mandal.objects.get(mid=value)
        except Mandal.DoesNotExist:
            raise serializers.ValidationError(
                f"Mandal with mid {value} does not exist."
            )
        return value

    def validate_delivery_village(self, value):
        try:
            MandalVillage.objects.get(vid=value)
        except MandalVillage.DoesNotExist:
            raise serializers.ValidationError(
                f"Village with vid {value} does not exist."
            )
        return value

    def validate_district(self, value):
        try:
            District.objects.get(did=value)
        except District.DoesNotExist:
            raise serializers.ValidationError(
                f"District with did {value} does not exist."
            )
        return value

    def validate_stockyard(self, value):
        try:
            StockYard.objects.get(name=value)
        except StockYard.DoesNotExist:
            raise serializers.ValidationError(
                f"StockYard with name '{value}' does not exist."
            )
        return value

    def create(self, validated_data):
        delivery_district_did = validated_data.pop("delivery_district")
        delivery_mandal_mid = validated_data.pop("delivery_mandal")
        delivery_village_vid = validated_data.pop("delivery_village")
        district_did = validated_data.pop("district")
        stockyard_name = validated_data.pop("stockyard")

        delivery_district_obj = District.objects.get(did=delivery_district_did)
        delivery_mandal_obj = Mandal.objects.get(mid=delivery_mandal_mid)
        delivery_village_obj = MandalVillage.objects.get(vid=delivery_village_vid)
        district_obj = District.objects.get(did=district_did)
        stockyard_obj = StockYard.objects.get(name=stockyard_name)

        booking = BookingMasterData.objects.create(
            delivery_district=delivery_district_obj,
            delivery_mandal=delivery_mandal_obj,
            delivery_village=delivery_village_obj,
            district=district_obj,
            stockyard=stockyard_obj,
            **validated_data,
        )

        return booking

    def update(self, instance, validated_data):
        if "delivery_district" in validated_data:
            delivery_district_did = validated_data.pop("delivery_district")
            instance.delivery_district = District.objects.get(did=delivery_district_did)

        if "delivery_mandal" in validated_data:
            delivery_mandal_mid = validated_data.pop("delivery_mandal")
            instance.delivery_mandal = Mandal.objects.get(mid=delivery_mandal_mid)

        if "delivery_village" in validated_data:
            delivery_village_vid = validated_data.pop("delivery_village")
            instance.delivery_village = MandalVillage.objects.get(
                vid=delivery_village_vid
            )

        if "district" in validated_data:
            district_did = validated_data.pop("district")
            instance.district = District.objects.get(did=district_did)

        if "stockyard" in validated_data:
            stockyard_name = validated_data.pop("stockyard")
            instance.stockyard = StockYard.objects.get(name=stockyard_name)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


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


class CreateBookingHistorySerializer(serializers.Serializer):

    booking_master = serializers.IntegerField(write_only=True)

    class Meta:
        model = BookingHistory
        fields = "__all__"


class BookingHistorySerializer(serializers.ModelSerializer):
    booking_master = BookingMasterDataSerializer()

    class Meta:
        model = BookingHistory
        fields = "__all__"
