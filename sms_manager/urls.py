from .views import OTPRecentUploadView, OTPListCreateView, OTPRetrieveUpdateDestroyView
from django.urls import path


urlpatterns = [
    path("recent/", OTPRecentUploadView.as_view(), name="recent_otp"),
    path("", OTPListCreateView.as_view(), name="list_otp"),
    path(
        "<int:pk>/",
        OTPRetrieveUpdateDestroyView.as_view(),
        name="retrieve_get_destroy_otp",
    ),
]
