from django.urls import path
from .views import (
    LoadInitialDataView,
    GetAllDistrictView,
    GetDistrictStockyard,
    GetDistrictMandal,
    GetMandalVillages,
)

urlpatterns = [
    path("load-data", LoadInitialDataView.as_view(), name="load_data"),
    path("districts", GetAllDistrictView.as_view(), name="get-districts"),
    path(
        "districts/<int:did>/stockyards",
        GetDistrictStockyard.as_view(),
        name="get-stockyards",
    ),
    path("districts/<int:did>/mandals", GetDistrictMandal.as_view(), name="get-mandal"),
    path(
        "districts/mandals/<int:mid>/villages",
        GetMandalVillages.as_view(),
        name="get-villages",
    ),
]
