import hashlib
from rest_framework import serializers
from .orm_models import Customer


def _hash_password(raw: str) -> str:
    """Simple SHA-256 hash. In production use bcrypt/argon2."""
    return hashlib.sha256(raw.encode()).hexdigest()


class CustomerRegisterSerializer(serializers.ModelSerializer):
    """Used for POST /api/customers/register/"""
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Customer
        fields = ['id', 'full_name', 'email', 'password', 'phone', 'address']
        read_only_fields = ['id']

    def validate_email(self, value):
        if Customer.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already registered.')
        return value

    def create(self, validated_data):
        raw_password = validated_data.pop('password')
        validated_data['password_hash'] = _hash_password(raw_password)
        return Customer.objects.create(**validated_data)


class CustomerLoginSerializer(serializers.Serializer):
    """Used for POST /api/customers/login/"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        try:
            customer = Customer.objects.get(email=email)
        except Customer.DoesNotExist:
            raise serializers.ValidationError('Invalid email or password.')

        if not customer.is_active:
            raise serializers.ValidationError('Account is deactivated.')

        if customer.password_hash != _hash_password(password):
            raise serializers.ValidationError('Invalid email or password.')

        attrs['customer'] = customer
        return attrs


class CustomerProfileSerializer(serializers.ModelSerializer):
    """Used for GET and PUT /api/customers/{id}/"""
    class Meta:
        model = Customer
        fields = [
            'id', 'full_name', 'email', 'phone', 'address',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'email', 'is_active', 'created_at', 'updated_at']


class CustomerUpdateSerializer(serializers.ModelSerializer):
    """Handles partial-safe PUT for profile update."""
    class Meta:
        model = Customer
        fields = ['full_name', 'phone', 'address']


class CustomerInternalSerializer(serializers.ModelSerializer):
    """Minimal read-only view used by internal service calls."""
    class Meta:
        model = Customer
        fields = ['id', 'full_name', 'email', 'phone', 'address', 'is_active']
