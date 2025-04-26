from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import register_user, login_user, create_property, list_properties, list_available_properties, get_property, update_property, delete_property, apply_to_property, view_applications_for_owner, tenant_applications, cancel_application, list_notifications, mark_notification_as_read, owner_dashboard, tenant_dashboard, list_payments, create_payment, update_payment_status, list_reviews, submit_review, update_review, list_all_applied_properties, properties_with_applicants, change_application_status

urlpatterns = [
    # User registration route
    path('register/', register_user, name='register'),
    # User login route
    path('login/', login_user, name='login'),
    
    # Property creation route (for owners or admins)
    path('create-property/', create_property, name='create_property'),
    
    # List properties for authenticated users (owners can view their own properties)
    path('my-properties/', list_properties, name='my-properties'),
    
    # List available properties for tenants
    path('properties/available/', list_available_properties, name='list-available-properties'),
    
    # Get specific property details by ID
    path('property/<int:pk>/', get_property, name='get-property'),
    
    # Update a property details by ID
    path('property/<int:pk>/edit/', update_property, name='update-property'),
    
    # Delete a property by ID
    path('property/<int:pk>/delete/', delete_property, name='delete-property'),
    
    # Route for tenants to apply for a property
    path('apply/<int:property_id>/', apply_to_property, name='apply-property'),
    
    # View all applications submitted by tenants for the property (only for owners)
    path('applications/', view_applications_for_owner, name='view-applications'),
    
    # View tenant-specific applications
    path('tenant/applications/', tenant_applications, name='tenant-applications'),
    
    # Route for tenants to cancel their application
    path('application/<int:pk>/cancel/', cancel_application, name='cancel-application'),
    
    # Route to change the status of an application (approve/reject) by the owner
    path('apply/change-status/<int:pk>/', change_application_status, name='change_application_status'),
    
    # List all notifications for a user
    path('notifications/', list_notifications, name='list-notifications'),
    
    # Mark a notification as read
    path('notifications/<int:pk>/read/', mark_notification_as_read, name='read-notification'),
    
    # Owner's dashboard route (to view stats and manage properties)
    path('owner/dashboard/', owner_dashboard, name='owner-dashboard'),
    
    # Tenant's dashboard route (to view applications, payments, etc.)
    path('tenant/dashboard/', tenant_dashboard, name='tenant-dashboard'),
    
    # List all payments made by tenants
    path('payments/', list_payments, name='list_payments'),
    
    # Create a payment for a specific property (tenant paying for property)
    path('payments/create/<int:property_id>/', create_payment, name='create_payment'),
    
    # Update the status of a payment (e.g., mark as completed)
    path('payments/update/<int:payment_id>/', update_payment_status, name='update_payment_status'),
    
    # List reviews for a specific property
    path('properties/<int:property_id>/reviews/', list_reviews, name='list-reviews'),
    
    # Submit a review for a property
    path('properties/<int:property_id>/reviews/submit/', submit_review, name='submit-review'),
    
    # Update an existing review for a property
    path('reviews/<int:review_id>/update/', update_review, name='update_review'),
    
    # List all properties a tenant has applied for
    path('properties/applied/', list_all_applied_properties, name='list-applied-properties'),
    
    # List properties that have applicants
    path('properties/with-applicants/', properties_with_applicants, name='properties_with_applicants'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Handle media files (images, documents, etc.)
