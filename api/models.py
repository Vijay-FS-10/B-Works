from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings

# User Model
class User(AbstractUser):
    # Choices for user type
    USER_TYPE_CHOICES = (
        ('owner', 'Owner'),
        ('tenant', 'Tenant'),
    )

    email = models.EmailField(unique=True)  # Ensures unique email for each user
    phone_number = models.CharField(max_length=20, blank=True)  # Optional phone number
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)  # Owner or Tenant

    # String representation of the user
    def __str__(self):
        return f"{self.email} ({self.user_type})"

# Property Model
class Property(models.Model):
    name = models.CharField(max_length=100)  # Name of the property
    address = models.TextField()  # Full address of the property
    city = models.CharField(max_length=50)  # City where the property is located
    state = models.CharField(max_length=50)  # State where the property is located
    zip_code = models.CharField(max_length=10)  # Zip code of the property
    is_available = models.BooleanField(default=True)  # Availability status of the property

    # Foreign key relationship to the User model (owner)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_properties",  # Reverse relationship name
        blank=True,
        null=True
    )

    # String representation of the property
    def __str__(self):
        return self.name

# Property Image Model
class PropertyImage(models.Model):
    # Link each image to a specific property
    property = models.ForeignKey(Property, related_name='property_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='property_images/')  # Upload images to a specific folder

    # String representation of the image
    def __str__(self):
        return f"Image for {self.property.name}"

# Application Model
class Application(models.Model):
    # Status choices for the application
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')  # Tenant applying for the property
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='applications')  # Property being applied for
    message = models.TextField(blank=True)  # Optional message from tenant
    applied_on = models.DateTimeField(auto_now_add=True)  # Date and time when the application was made
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Application status

    # Prevent duplicate applications for the same property by the same tenant
    class Meta:
        unique_together = ('tenant', 'property')

    # String representation of the application
    def __str__(self):
        return f"{self.tenant.username} applied for {self.property.name}"

# Notification Model
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')  # The user receiving the notification
    message = models.TextField()  # The content of the notification
    is_read = models.BooleanField(default=False)  # Read/unread status
    created_at = models.DateTimeField(auto_now_add=True)  # Date and time when the notification was created

    # String representation of the notification
    def __str__(self):
        return f"To: {self.user.username} - {self.message[:30]}"

# Payment Model
class Payment(models.Model):
    # Choices for payment status
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    # Choices for payment methods
    PAYMENT_METHOD_CHOICES = (
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
    )

    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')  # The tenant making the payment
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='payments')  # Property for which payment is made
    application = models.ForeignKey(Application, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')  # Associated application (nullable)
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Amount of the payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='upi')  # Method of payment
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')  # Payment status
    payment_date = models.DateTimeField(auto_now_add=True)  # Date and time of payment
    receipt = models.FileField(upload_to='payment_receipts/', null=True, blank=True)  # Payment receipt (optional)

    # String representation of the payment
    def __str__(self):
        return f"{self.tenant.username} paid ₹{self.amount} for {self.property.name} ({self.status})"

# Property Review Model
class PropertyReview(models.Model):
    property = models.ForeignKey('Property', related_name='reviews', on_delete=models.CASCADE)  # The property being reviewed
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # The tenant leaving the review
    rating = models.IntegerField()  # Rating from 1 to 5
    review = models.TextField(blank=True)  # Optional written review
    created_at = models.DateTimeField(auto_now_add=True)  # Date and time when the review was created

    # Prevent more than one review per tenant per property
    class Meta:
        unique_together = ('property', 'tenant')

    # String representation of the review
    def __str__(self):
        return f"{self.tenant.username} rated {self.property.name} - {self.rating}★"
