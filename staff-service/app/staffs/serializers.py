from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import Staff


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = [
            'id',
            'staff_code',
            'full_name',
            'email',
            'role',
            'department',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'is_active', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Staff
        fields = [
            'staff_code',
            'full_name',
            'email',
            'password',
            'role',
            'department',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['password_hash'] = make_password(password)
        return Staff.objects.create(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
