from rest_framework import serializers
from .models import User, Property, Application, Notification, PropertyImage, Payment, PropertyReview
from django.contrib.auth.hashers import make_password

# Serializer for PropertyImage model
class PropertyImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)  # Automatically generates the image URL

    class Meta:
        model = PropertyImage
        fields = ['id', 'image']  # Fields to be serialized for PropertyImage model

    # Custom representation for the image field
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')  # Get request object to build absolute URL
        if request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation


# Serializer for User Registration
class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'phone_number', 'user_type']
        extra_kwargs = {
            'password': {'write_only': True}  # Password field should not be read-only
        }

    # Overriding create method to hash the password before saving the user
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])  # Hash the password
        return super().create(validated_data)


# Serializer for Property model
class PropertySerializer(serializers.ModelSerializer):
    application_count = serializers.SerializerMethodField()  # Custom field to count applications for the property
    images = PropertyImageSerializer(source='property_images', many=True, read_only=True)  # Nested images field
    owner = serializers.ReadOnlyField(source='user.username')  # Read-only field for property owner username

    class Meta:
        model = Property
        fields = ['id', 'name', 'address', 'city', 'state', 'zip_code', 'is_available', 'images', 'application_count', 'owner']

    # Method to get the number of applications for a property
    def get_application_count(self, obj):
        return Application.objects.filter(property=obj).count()


# Serializer for Application model
class ApplicationSerializer(serializers.ModelSerializer):
    tenant = serializers.ReadOnlyField(source='tenant.username')  # Tenant's username
    status = serializers.CharField(read_only=True)  # Status field (read-only)

    class Meta:
        model = Application
        fields = ['id', 'tenant', 'property', 'message', 'applied_on', 'status']


# Serializer for Notification model
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'is_read', 'created_at']  # Fields related to notifications


# Serializer for Payment model
class PaymentSerializer(serializers.ModelSerializer):
    property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all())  # Link to Property model
    tenant = serializers.ReadOnlyField(source='tenant.username')  # Tenant's username
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)  # Payment amount
    status = serializers.CharField(default='pending')  # Default payment status
    paid_at = serializers.DateTimeField(read_only=True, required=False)  # Read-only payment date

    class Meta:
        model = Payment
        fields = ['id', 'tenant', 'property', 'amount', 'status', 'paid_at']

    # Method to handle additional logic before creating the payment
    def create(self, validated_data):
        payment = super().create(validated_data)
        return payment


# Serializer for PropertyReview model
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyReview
        fields = ['id', 'property', 'tenant', 'rating', 'review', 'created_at']  # Fields for review serialization
        read_only_fields = ['id', 'property', 'tenant', 'created_at']  # Make some fields read-only

    # Custom validation for review field (non-empty)
    def validate_review(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Review cannot be empty.")  # Ensure the review is not empty
        return value
