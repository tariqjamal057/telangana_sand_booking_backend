from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from django.conf import settings
import json

from booking.models import District, StockYard, Mandal, MandalVillage


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
