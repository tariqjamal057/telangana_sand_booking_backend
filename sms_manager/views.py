from .models import UserOTP
from .serializers import UserOTPSerializer
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

class OTPListCreateView(ListCreateAPIView):
    queryset = UserOTP.objects.all()
    serializer_class = UserOTPSerializer

class OTPRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = UserOTP.objects.all()
    serializer_class = UserOTPSerializer

class OTPRecentUploadView(APIView):
    def get(self, request):
        try:
            latest_otp = UserOTP.objects.latest('otp_created_at')
            serializer = UserOTPSerializer(latest_otp)
            return Response(serializer.data)
        except UserOTP.DoesNotExist:
            return Response({'error': 'No OTP records found.'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

        
