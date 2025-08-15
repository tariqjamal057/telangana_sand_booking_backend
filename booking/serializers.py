from rest_framework import serializers
from .models import District, StockYard, Mandal, MandalVillage


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
