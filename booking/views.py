from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from django.conf import settings
import json


class LoadInitialDataView(APIView):
    def get(self, request):
        try:
            with open('booking/fixtures/districts.json') as f:
                districts = json.load(f)            

            return Response(districts, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
