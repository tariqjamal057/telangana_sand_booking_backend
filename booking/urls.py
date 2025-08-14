from django.urls import path
from .views import LoadInitialDataView

urlpatterns = [
    path('load-data', LoadInitialDataView.as_view(), name='load-data')
]
