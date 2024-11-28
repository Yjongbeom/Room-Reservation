from django.contrib.auth import authenticate
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, TokenError, AccessToken

from .models import Reservation, Users
from .serializers import ReservationSerializer, LoginSerializer, UsersSerializer

from datetime import datetime
import time


def copy_request_data(data):
    req_data = {}

    print(data)
    for key, value in data.items():
        req_data[key] = value

    return req_data

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def create(self, request, *args, **kwargs):
        req_data = copy_request_data(request.data)

        end_time_str = request.data.get('end_time')
        end_time_obj = datetime.strptime(end_time_str, '%H:%M')
        end_time_formatted = end_time_obj.strftime('%H:%M:%S')

        start_time_str = request.data.get('start_time')
        start_time_obj = datetime.strptime(start_time_str, '%H:%M')
        start_time_formatted = start_time_obj.strftime('%H:%M:%S')

        #예약한 시간에 다시 예약할려하면 예외처리

        req_data["start_time"] = start_time_formatted
        req_data["end_time"] = end_time_formatted

        queryset_endtime = Reservation.objects.filter(building=request.data.get('building'), floor=request.data.get('floor'), day=request.data.get('day'), month=request.data.get('month'), year=request.data.get('year'), room=request.data.get('room'), end_time=request.data.get('end_time'))
        queryset_starttime = Reservation.objects.filter(building=request.data.get('building'), floor=request.data.get('floor'), day=request.data.get('day'), month=request.data.get('month'), year=request.data.get('year'), room=request.data.get('room'), start_time=request.data.get('start_time'))

        if len(queryset_starttime) > 0 or len(queryset_endtime) > 0:
            serializer = self.get_serializer(data=req_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        return Response({'message': '이미 존재하는 예약입니다.'}, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request, *args, **kwargs):
        # Filter reservations based on the query parameters
        queryset = Reservation.objects.filter(
            building=request.query_params.get('building'),
            floor=request.query_params.get('floor'),
            day=request.query_params.get('day'),
            month=request.query_params.get('month'),
            year=request.query_params.get('year')
        )

        for query in list(queryset):
            if query.end_time < datetime.now().time() and datetime.now().date() == datetime(query.year, query.month, query.day).date():
                print(f"Deleting expired reservation: {query}")
                query.delete()

        updated_queryset = Reservation.objects.filter(
            building=request.query_params.get('building'),
            floor=request.query_params.get('floor'),
            day=request.query_params.get('day'),
            month=request.query_params.get('month'),
            year=request.query_params.get('year')
        )

        page = self.paginate_queryset(updated_queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(updated_queryset, many=True)
        return Response(serializer.data)
    
class ReservationDetailViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    
    def list(self, request, *args, **kwargs):
        queryset = Reservation.objects.filter(building=request.query_params.get('building'), floor=request.query_params.get('floor'), day=request.query_params.get('day'), month=request.query_params.get('month'), year=request.query_params.get('year'), room=request.query_params.get('room'))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    

class LoginViewSet(viewsets.ModelViewSet):
    serializer_class = LoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        studentNumber = request.data.get('studentNumber')
        password = request.data.get('password')

        if studentNumber is None or password is None:
            return Response(status=400)

        user = authenticate(username=studentNumber, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)

            user.refresh_token = str(refresh)
            user.save()

            return Response({
                'access': str(refresh.access_token),
                'studentNumber': user.studentNumber,
                'name': user.name,
                'phone': user.phone,
            }, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    def retrieve(self, request, *args, **kwargs):
        access_token = request.data.get('access_token')

        if not access_token:
            return Response({"detail": "access token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decode_token = AccessToken(access_token)
            user_id = decode_token['user_id']

            user = Users.objects.get(pk=user_id)

            return Response({
                'studentNumver': user.studentNumber,
                'name': user.name,
                'phone': user.phone,
            }, status=status.HTTP_200_OK)

        except Users.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except TokenError:
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RegisterViewSet(viewsets.ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UsersSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response({
            'studentNumber': user.studentNumber,
            'name': user.name,
            'phone': user.phone,
        }, status=status.HTTP_201_CREATED)

class TokenRefreshViewSet(viewsets.ViewSet):
    def create(self, request, *args, **kwargs):
        access_token = request.data.get('access_token')

        if not access_token:
            return Response({"detail": "access token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decode_token = AccessToken(access_token)
            user_id = decode_token['user_id']

            user = Users.objects.get(pk=user_id)

            refresh_token = user.refresh_token
            token = RefreshToken(refresh_token)

            return Response({
                'access': str(token.access_token),
            }, status=status.HTTP_200_OK)

        except Users.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except TokenError:
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)