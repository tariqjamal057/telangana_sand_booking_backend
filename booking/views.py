import datetime
import random
from rest_framework.views import APIView
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    ListAPIView,
)
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import json

from booking.selenium_script import SandBookingScript

from .models import (
    BookingHistory,
    BookingMasterData,
    BookingUserCredential,
    District,
    StockYard,
    Mandal,
    MandalVillage,
)
from .serializers import (
    BookingHistorySerializer,
    CreateBookingMasterDataSerializer,
    DistrictSerializer,
    DistrictStockyardSerializer,
    MandalSerializer,
    MandalVillageSerializer,
    BookingUserCredentialSerializer,
    BookingMasterDataSerializer,
)


class LoadInitialDataView(APIView):
    def get(self, request):
        try:
            with open("booking/fixtures/districts.json") as f:
                districts = json.load(f)

            with open("booking/fixtures/district_stockyards.json") as f:
                district_stockyards = json.load(f)

            with open("booking/fixtures/distrit_mandal.json") as f:
                district_mandals = json.load(f)

            with open("booking/fixtures/district_mandal_villages.json") as f:
                district_mandal_villages = json.load(f)

            MandalVillage.objects.all().delete()
            Mandal.objects.all().delete()
            StockYard.objects.all().delete()
            District.objects.all().delete()

            # load districts
            District.objects.bulk_create(
                [
                    District(
                        name=district["name"],
                        did=district["did"],
                    )
                    for district in districts
                ]
            )

            # load district stockyards
            for district in district_stockyards:
                district_obj = District.objects.get(did=district["districtId"])
                StockYard.objects.bulk_create(
                    [
                        StockYard(
                            name=stockyard["stockyard_name"],
                            district=district_obj,
                            contact_person_name=stockyard["contact_person"],
                            contact_person_number=stockyard["contact_number"],
                            address=stockyard["address"],
                            sand_quality=stockyard["sand_quality"],
                            sand_price=stockyard["sand_price"],
                        )
                        for stockyard in district["stockyards"]
                    ]
                )

            # load district mandals
            for district in district_mandals:
                district_obj = District.objects.get(did=district["districtId"])
                Mandal.objects.bulk_create(
                    [
                        Mandal(
                            name=mandal["name"],
                            district=district_obj,
                            mid=mandal["did"],
                        )
                        for mandal in district["mandals"]
                    ]
                )

            # load district mandal villages
            for mandal in district_mandal_villages:
                mandal_obj = Mandal.objects.get(mid=mandal["mandalId"])
                MandalVillage.objects.bulk_create(
                    [
                        MandalVillage(
                            name=mandal_village["name"],
                            mandal=mandal_obj,
                            vid=mandal_village["did"],
                        )
                        for mandal_village in mandal["villages"]
                    ]
                )

            return Response(
                {"message": "Data loaded successfully"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetAllDistrictView(APIView):
    def get(self, request):
        try:
            districts = District.objects.all()
            serializer = DistrictSerializer(districts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetDistrictStockyard(APIView):
    def get(self, request, did):
        try:
            district = District.objects.get(did=did)
            stockyards = StockYard.objects.filter(district=district)
            serializer = DistrictStockyardSerializer(stockyards, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetDistrictMandal(APIView):
    def get(self, request, did):
        try:
            district = District.objects.get(did=did)
            mandals = Mandal.objects.filter(district=district)
            serializer = MandalSerializer(mandals, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetMandalVillages(APIView):
    def get(self, request, mid):
        try:
            mandal = Mandal.objects.get(mid=mid)
            villages = MandalVillage.objects.filter(mandal=mandal)
            serializer = MandalVillageSerializer(villages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateListUser(ListCreateAPIView):
    queryset = BookingUserCredential.objects.all()
    serializer_class = BookingUserCredentialSerializer


class BookingUserRetriveUpdateView(RetrieveUpdateAPIView):
    queryset = BookingUserCredential.objects.all()
    serializer_class = BookingUserCredentialSerializer


class CreateListBookingMasterData(ListCreateAPIView):
    queryset = BookingMasterData.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateBookingMasterDataSerializer
        return BookingMasterDataSerializer


class BookingMasterDataRetriveUpdateView(RetrieveUpdateAPIView):
    queryset = BookingMasterData.objects.all()

    def get_serializer_class(self):
        if self.request.method == "PUT":
            return CreateBookingMasterDataSerializer
        return BookingMasterDataSerializer


def get_new_proxy():
    PROXY_POOL = [
        "http://bhaktabhim.duckdns.org:8002",
        "http://bhaktabhim.duckdns.org:8003",
        "http://bhaktabhim.duckdns.org:8004",
        "http://bhaktabhim.duckdns.org:8005",
        "http://bhaktabhim.duckdns.org:8006",
    ]
    return random.choice(PROXY_POOL)


class StartBookingAutomationView(APIView):
    def post(self, request):
        print(request.data)
        booking_master_id = request.data.get("booking_master_id")
        if not booking_master_id:
            return Response(
                {"error": "booking_master_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            booking_master = BookingMasterData.objects.get(id=booking_master_id)
        except BookingMasterData.DoesNotExist:
            return Response(
                {"error": "Invalid booking_master_id"}, status=status.HTTP_404_NOT_FOUND
            )

        proxy = get_new_proxy()
        history = BookingHistory.objects.create(
            booking_master=booking_master, proxy=proxy, status="running"
        )

        try:
            script = SandBookingScript(proxy=proxy, booking_master_id=booking_master.id)
            script.initial_setup()
            script.run()
            history.status = "success"
            history.message = "Booking completed successfully"
        except Exception as e:
            history.status = "failed"
            history.message = str(e)
        finally:
            history.ended_at = datetime.datetime.now()
            history.save()

        return Response(
            BookingHistorySerializer(history).data, status=status.HTTP_200_OK
        )


class BookingHistoryView(ListAPIView):
    queryset = BookingHistory.objects.all()
    serializer_class = BookingHistorySerializer
