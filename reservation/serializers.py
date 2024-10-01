from .models import *
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['studentNumber', 'password', 'name', 'phone']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = Users(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('studentNumber')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise serializers.ValidationError("Invalid login credentials")

            refresh = RefreshToken.for_user(user)
            return {
                'access': str(refresh.access_token),
                'studentNumber': user.username
            }
        else:
            raise serializers.ValidationError("Both username and password are required")

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = "__all__"
