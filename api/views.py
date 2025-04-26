from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from decimal import Decimal
from django.db import IntegrityError,transaction
from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import User,Property,Application,Notification,PropertyImage,Payment,PropertyReview
from .serializers import UserRegistrationSerializer,PropertySerializer,ApplicationSerializer,NotificationSerializer,PaymentSerializer,ReviewSerializer
from rest_framework.permissions import AllowAny

@api_view(['POST'])  # This view accepts only POST requests
@permission_classes([AllowAny])  # Allows unauthenticated users to access this view (for registration)
def register_user(request):
    # Initialize serializer with request data
    serializer = UserRegistrationSerializer(data=request.data)
    
    #  Validate the input data
    if serializer.is_valid():
        try:
            # Save the user if validation passes
            user = serializer.save()
            
            # Generate or retrieve authentication token for the new user
            token, created = Token.objects.get_or_create(user=user)

            #  Return success response with user data and token
            return Response({
                "StatusCode": 6000,
                "data": {
                    "title": "Success",
                    "message": "User registered successfully",
                    "response": {
                        "user": serializer.data,  # Serialized user data
                        "token": token.key        # Auth token for login
                    }
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            #  Catch unexpected errors during user creation
            return Response({
                "StatusCode": 6002,
                "data": {
                    "title": "Error",
                    "message": "Something went wrong while creating the user.",
                    "error": str(e)  # Error message for debugging
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #  Return validation errors if data is invalid
    return Response({
        "StatusCode": 6001,
        "data": {
            "title": "Validation Failed",
            "message": "Invalid input data",
            "errors": serializer.errors  # Detailed field-level errors
        }
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])  # This view accepts only POST requests
@permission_classes([AllowAny])  # Anyone (even unauthenticated users) can access this view
def login_user(request):
    # Extract email and password from request data
    email = request.data.get('email')
    password = request.data.get('password')

    #  Check if both email and password are provided
    if email is None or password is None:
        return Response({
            "StatusCode": 6001,
            "data": {
                "title": "Validation Failed",
                "message": "Email and password are required."  # Missing input
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        #  Try to get the user by email
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        #  If user with given email does not exist
        return Response({
            "StatusCode": 6005,
            "data": {
                "title": "Login Failed",
                "message": "Invalid email or password."
            }
        }, status=status.HTTP_401_UNAUTHORIZED)

    #  Check if the password is correct
    if not user.check_password(password):
        return Response({
            "StatusCode": 6005,
            "data": {
                "title": "Login Failed",
                "message": "Invalid email or password."  # Incorrect password
            }
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        #  Generate or retrieve auth token
        token, created = Token.objects.get_or_create(user=user)

        #  Return successful login response with user details and token
        return Response({
            "StatusCode": 6000,
            "data": {
                "title": "Success",
                "message": "Login successful",
                "response": {
                    "token": token.key,         # Auth token for future requests
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "user_type": user.user_type  # Custom user field
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        #  Handle any unexpected errors during login
        return Response({
            "StatusCode": 6002,
            "data": {
                "title": "Error",
                "message": "Something went wrong during login.",
                "error": str(e)  # Include error for debugging
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])  # This view only accepts POST requests
@permission_classes([IsAuthenticated])  # Only logged-in users can access this view
def create_property(request):
    #  Extract relevant property fields from request data (excluding images)
    property_data = {
        'name': request.data.get('name'),
        'address': request.data.get('address'),
        'city': request.data.get('city'),
        'state': request.data.get('state'),
        'zip_code': request.data.get('zip_code'),
        'is_available': request.data.get('is_available'),
    }

    #  Validate property data using the PropertySerializer
    serializer = PropertySerializer(data=request.data)

    if serializer.is_valid():
        #  Save the property instance and associate it with the current user
        property_instance = serializer.save(user=request.user)

        #  Handle multiple image uploads (if any)
        images = request.FILES.getlist('images')  # Get list of uploaded image files
        uploaded_images = []

        if images:
            for image in images:
                # Save each image with reference to the created property
                img_instance = PropertyImage.objects.create(property=property_instance, image=image)
                # Store absolute image URLs for frontend usage
                uploaded_images.append(request.build_absolute_uri(img_instance.image.url))

        #  Successful response with property details and uploaded image URLs
        return Response({
            'message': 'Property created successfully',
            'property': PropertySerializer(property_instance).data,
            'images': uploaded_images if uploaded_images else "No images uploaded"
        }, status=status.HTTP_201_CREATED)

    #  Return validation errors if serializer is not valid
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])  # LIST PROPERTIES BASED ON ROLES AND SEARCH FILTERING
@permission_classes([IsAuthenticated])
def list_properties(request):
    try:
        user = request.user
        properties = Property.objects.all()

        # 🔍 Search and filter parameters
        city = request.query_params.get('city')
        state = request.query_params.get('state')
        zip_code = request.query_params.get('zip_code')
        name = request.query_params.get('name')
        user_id = request.query_params.get('user_id')

        # 🧠 Apply filters
        if city:
            properties = properties.filter(city__icontains=city)
        if state:
            properties = properties.filter(state__icontains=state)
        if zip_code:
            properties = properties.filter(zip_code__icontains=zip_code)
        if name:
            properties = properties.filter(name__icontains=name)
        if user_id:
            properties = properties.filter(user__id=user_id)

        # 🎯 Role-based property filtering
        if user.user_type == 'owner':
            properties = properties.filter(user=user)
        elif user.user_type == 'tenant':
            applied_property_ids = Application.objects.filter(tenant=user).values_list('property_id', flat=True)
            properties = properties.filter(id__in=applied_property_ids)

        if not properties.exists():
            return Response({
                "StatusCode": 6002,
                "data": {
                    "title": "No Properties Found",
                    "properties": []
                }
            }, status=status.HTTP_200_OK)

        serializer = PropertySerializer(properties, many=True, context={'request': request})

        return Response({
            "StatusCode": 6000,
            "data": {
                "title": "Success",
                "properties": serializer.data
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "StatusCode": 6005,
            "data": {
                "title": "Something Went Wrong",
                "message": str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])  #  This view handles only GET requests
@permission_classes([AllowAny])  #  Anyone can access this view (tenants, owners, etc.)
# If you want only logged-in tenants to view, change to: [IsAuthenticated]
def list_available_properties(request):
    #  Query all properties where 'is_available' is True
    properties = Property.objects.filter(is_available=True)

    #  Serialize the queryset with context (for generating full image URLs, etc.)
    serializer = PropertySerializer(properties, many=True, context={'request': request})

    #  Return serialized property data
    return Response(serializer.data)


@api_view(['GET'])  #  This view accepts only GET requests (to fetch a single property)
@permission_classes([IsAuthenticated])  #  Only authenticated users can access this view
def get_property(request, pk):
    try:
        # 🔍 Try to get the property by its primary key (id)
        try:
            property = Property.objects.get(pk=pk)
        except Property.DoesNotExist:
            #  If not found, return 404 with a custom error message
            return Response({
                "StatusCode": 6002,
                "data": {
                    "title": "Not Found",
                    "message": "Property not found"
                }
            }, status=status.HTTP_404_NOT_FOUND)

        #  Optional: Only allow the owner of the property to view it
        if property.user != request.user:
            return Response({
                "StatusCode": 6001,
                "data": {
                    "title": "Permission Denied",
                    "message": "You do not have permission to view this property."
                }
            }, status=status.HTTP_403_FORBIDDEN)

        #  If the user is authorized, serialize and return the property
        serializer = PropertySerializer(property, context={'request': request})
        return Response({
            "StatusCode": 6000,
            "data": {
                "title": "Success",
                "property": serializer.data
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        #  If an unexpected error occurs, return 500 with error message
        return Response({
            "StatusCode": 6005,
            "data": {
                "title": "Error",
                "message": str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])  #  Accepts PUT (full update) and PATCH (partial update) methods
@permission_classes([IsAuthenticated])  #  Only authenticated users can update a property
def update_property(request, pk):
    try:
        # 🔍 Try to get the property by primary key (id)
        try:
            property = Property.objects.get(pk=pk)
        except Property.DoesNotExist:
            #  Return 404 if property is not found
            return Response({
                "StatusCode": 6002,
                "data": {
                    "title": "Not Found",
                    "message": "Property not found"
                }
            }, status=status.HTTP_404_NOT_FOUND)

        #  Ensure that only the owner of the property can update it
        if property.user != request.user:
            return Response({
                "StatusCode": 6001,
                "data": {
                    "title": "Permission Denied",
                    "message": "You do not have permission to edit this property."
                }
            }, status=status.HTTP_403_FORBIDDEN)

        #  Validate and update the property details
        serializer = PropertySerializer(property, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()

            #  If new images are uploaded, save them
            if 'images' in request.FILES:
                images = request.FILES.getlist('images')
                for image in images:
                    PropertyImage.objects.create(property=property, image=image)

            #  Re-serialize to include newly added images
            updated_serializer = PropertySerializer(property, context={'request': request})
            return Response({
                "StatusCode": 6000,
                "data": {
                    "title": "Success",
                    "message": "Property updated successfully",
                    "property": updated_serializer.data
                }
            }, status=status.HTTP_200_OK)

        #  Return validation errors if the data is not valid
        return Response({
            "StatusCode": 6001,
            "data": {
                "title": "Validation Failed",
                "message": "Invalid input data",
                "errors": serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        #  Catch unexpected exceptions and return 500 error
        return Response({
            "StatusCode": 6005,
            "data": {
                "title": "Error",
                "message": str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['DELETE'])  #  Allows only DELETE requests to this endpoint
@permission_classes([IsAuthenticated])  #  Only authenticated users can delete a property
def delete_property(request, pk):
    try:
        #  Try to fetch the property by primary key (id)
        property = Property.objects.get(pk=pk)
    except Property.DoesNotExist:
        #  If property doesn't exist, return a 404 error
        return Response({'error': 'Property not found'}, status=404)

    #  Only the owner of the property can delete it
    if property.user != request.user:
        return Response({'error': 'You do not have permission to delete this property.'}, status=403)

    #  Delete the property from the database
    property.delete()
    return Response({'message': 'Property deleted successfully'}, status=200)



@api_view(['POST'])  #  Accepts only POST requests
@permission_classes([IsAuthenticated])  #  Only authenticated users can apply
def apply_to_property(request, property_id):
    #  Check if the user is a tenant
    if request.user.user_type != 'tenant':
        return Response({
            'code': 6001,
            'error': 'Only tenants can apply for properties.'
        }, status=status.HTTP_403_FORBIDDEN)

    #  Prevent duplicate applications for the same property by the same tenant
    if Application.objects.filter(property_id=property_id, tenant=request.user).exists():
        return Response({
            'code': 6002,
            'error': 'You have already applied to this property.'
        }, status=status.HTTP_400_BAD_REQUEST)

    #  Prepare data for the application (optional message included)
    data = {
        'property': property_id,
        'message': request.data.get('message', '')
    }

    # 🛠️ Validate application data using the serializer
    serializer = ApplicationSerializer(data=data)
    if serializer.is_valid():
        try:
            #  Save the application with the current user as tenant
            serializer.save(tenant=request.user)
            return Response({
                'code': 6000,
                'message': 'Application submitted successfully',
                'application': serializer.data
            }, status=status.HTTP_201_CREATED)

        except IntegrityError:
            #  In case of unique constraint violation or duplicate entry
            return Response({
                'code': 6003,
                'error': 'Duplicate application not allowed.'
            }, status=status.HTTP_400_BAD_REQUEST)

    #  If serializer is not valid, return errors
    return Response({
        'code': 6005,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])  #  Accepts only GET requests
@permission_classes([IsAuthenticated])  #  Only authenticated users can access
def view_applications_for_owner(request):
    #  Ensure the user is an owner
    if request.user.user_type != 'owner':
        return Response({
            'code': 6001,
            'status': False,
            'message': 'Only owners can view applications.'
        }, status=403)

    #  Get all properties owned by the user
    properties = Property.objects.filter(user=request.user)

    #  No properties listed by owner
    if not properties.exists():
        return Response({
            'code': 6002,
            'status': False,
            'message': 'You have not listed any properties.'
        }, status=200)

    #  Retrieve applications for the listed properties
    applications = Application.objects.filter(property__in=properties)

    # No applications found
    if not applications.exists():
        return Response({
            'code': 6005,
            'status': False,
            'message': 'No applications found for your properties.'
        }, status=200)

    #  Serialize and return the applications
    serializer = ApplicationSerializer(applications, many=True)
    return Response({
        'code': 6000,
        'status': True,
        'message': 'Applications retrieved successfully.',
        'applications': serializer.data
    }, status=200)


@api_view(['GET'])  #  Accepts only GET requests
@permission_classes([IsAuthenticated])  #  Only authenticated users can access
def tenant_applications(request):
    #  Ensure the user is a tenant
    if request.user.user_type != 'tenant':
        return Response({
            'code': 6001,
            'status': False,
            'message': 'Only tenants can view their applications.'
        }, status=status.HTTP_403_FORBIDDEN)

    #  Fetch all applications made by the tenant
    applications = Application.objects.filter(tenant=request.user)

    #  Handle case when no applications are found
    if not applications.exists():
        return Response({
            'code': 6005,
            'status': False,
            'message': 'No applications found.'
        }, status=status.HTTP_200_OK)

    #  Serialize and return the applications
    serializer = ApplicationSerializer(applications, many=True)
    return Response({
        'code': 6000,
        'status': True,
        'message': 'Applications retrieved successfully.',
        'applications': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['DELETE'])  # 🗑️ Accepts only DELETE requests
@permission_classes([IsAuthenticated])  # 🔐 Only authenticated users can access
def cancel_application(request, pk):
    try:
        # 🔍 Find the application by primary key and ensure it's for the current tenant
        application = Application.objects.get(id=pk, tenant=request.user)
    except Application.DoesNotExist:
        # ❌ Application doesn't exist or not related to the user
        return Response({
            'code': 6005,
            'status': False,
            'message': 'Application not found.'
        }, status=status.HTTP_404_NOT_FOUND)

    # 🔒 Ensure that the application is in 'pending' status before cancellation
    if application.status != 'pending':
        return Response({
            'code': 6002,
            'status': False,
            'message': 'Only pending applications can be cancelled.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # 🗑️ Delete the application if valid
    application.delete()
    return Response({
        'code': 6000,
        'status': True,
        'message': 'Application cancelled successfully.'
    }, status=status.HTTP_200_OK)

# Allows only PATCH HTTP method for updating application status
@api_view(['PATCH'])  
# Restricts access to only authenticated users
@permission_classes([IsAuthenticated])
def change_application_status(request, pk):
    # Check if the user is an owner; only owners can change application statuses
    if request.user.user_type != 'owner':
        return Response({
            'code': 6001,
            'status': False,
            'message': 'Only owners can update application status.'
        }, status=status.HTTP_403_FORBIDDEN)  # Return 403 Forbidden if not owner

    try:
        # Try to retrieve the application by ID
        application = Application.objects.get(id=pk)
    except Application.DoesNotExist:
        # Return 404 if application does not exist
        return Response({
            'code': 6005,
            'status': False,
            'message': 'Application not found.'
        }, status=status.HTTP_404_NOT_FOUND)

    # Ensure the application belongs to a property owned by the current user
    if application.property.user != request.user:
        return Response({
            'code': 6002,
            'status': False,
            'message': 'You do not own this property.'
        }, status=status.HTTP_403_FORBIDDEN)  # Forbidden if user doesn't own the property

    # Get the new status value from the request data
    status_choice = request.data.get('status')
    # Validate the status value — only 'approved' or 'rejected' are allowed
    if status_choice not in ['approved', 'rejected']:
        return Response({
            'code': 6003,
            'status': False,
            'message': 'Invalid status. Use "approved" or "rejected".'
        }, status=status.HTTP_400_BAD_REQUEST)  # Return 400 Bad Request for invalid status

    # Use a database transaction to ensure all operations below are atomic (all succeed or none)
    with transaction.atomic():
        # Update the application's status
        application.status = status_choice
        application.save()  # Save the updated status

        # If the application is approved
        if status_choice == 'approved':
            # Mark the property as no longer available
            application.property.is_available = False
            application.property.save()

            # Get all other pending applications for the same property (excluding the approved one)
            other_pending_apps = Application.objects.filter(
                property=application.property,
                status='pending'
            ).exclude(pk=application.pk)

            # Loop through all other pending applications
            for app in other_pending_apps:
                app.status = 'rejected'  # Set their status to rejected
                app.save()  # Save changes to the database

                # Create a notification for each rejected tenant
                Notification.objects.create(
                    user=app.tenant,  # Send to the tenant
                    message=f"Your application for '{application.property.name}' was rejected as another tenant was approved."
                )

        # Create a notification for the tenant whose application was approved or rejected
        Notification.objects.create(
            user=application.tenant,  # Send to the main tenant
            message=f"Your application for '{application.property.name}' was {status_choice}."
        )

    # Return a success response with the status
    return Response({
        'code': 6000,
        'status': True,
        'message': f'Application {status_choice} successfully.'
    }, status=status.HTTP_200_OK)  # 200 OK for successful status change
# Allow only GET requests to this view
@api_view(['GET'])
# Ensure the user is authenticated to access their notifications
@permission_classes([IsAuthenticated])
def list_notifications(request):
    # Fetch all notifications for the logged-in user, ordered by most recent
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Serialize the queryset into a JSON-compatible format
    serializer = NotificationSerializer(notifications, many=True)

    # Return the serialized data with a success message
    return Response({
        'code': 6000,
        'status': True,
        'message': 'Notifications retrieved successfully.',
        'data': serializer.data
    }, status=200)  # HTTP 200 OK



# Allow only PATCH requests to this view
@api_view(['PATCH'])
# Ensure the user is authenticated
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, pk):
    try:
        # Attempt to retrieve the notification by its primary key (ID) and make sure it belongs to the user
        notification = Notification.objects.get(pk=pk, user=request.user)

        # Set the is_read flag to True
        notification.is_read = True
        notification.save()  # Save the updated status

        # Return a success response
        return Response({
            'code': 6000,
            'status': True,
            'message': 'Notification marked as read.'
        }, status=200)  # HTTP 200 OK
    except Notification.DoesNotExist:
        # If the notification doesn't exist or doesn't belong to the user, return a 404
        return Response({
            'code': 6001,
            'status': False,
            'message': 'Notification not found.'
        }, status=404)  # HTTP 404 Not Found
    

# Allow only GET requests to this view (for reading dashboard data)
@api_view(['GET'])  # OWNER DASHBOARD
# Only authenticated users can access this view
@permission_classes([IsAuthenticated])
def owner_dashboard(request):
    # Check if the logged-in user is an owner
    if request.user.user_type != 'owner':
        # Return a 403 Forbidden if not an owner
        return Response({
            'code': 6001,
            'status': False,
            'message': 'Only property owners can access this dashboard.'
        }, status=403)

    # Fetch all properties that belong to this owner
    properties = Property.objects.filter(user=request.user)
    # Count total number of properties owned by the user
    total_properties = properties.count()

    # Fetch all tenant applications related to the owner’s properties
    applications = Application.objects.filter(property__in=properties)
    # Count total number of applications received
    total_applications = applications.count()

    # Count how many applications have been approved
    approved = applications.filter(status='approved').count()
    # Count how many applications are still pending
    pending = applications.filter(status='pending').count()
    # Count how many applications were rejected
    rejected = applications.filter(status='rejected').count()

    # Count how many properties are still available for rent
    available_properties = properties.filter(is_available=True).count()
    # Rented properties = total - available
    rented_properties = total_properties - available_properties

    # Return all dashboard data in a structured JSON response
    return Response({
        'code': 6000,
        'status': True,
        'message': 'Dashboard data fetched successfully.',
        'data': {
            'total_properties': total_properties,  # Total number of properties owned
            'total_applications': total_applications,  # Total applications received
            'applications': {
                'approved': approved,  # Number of approved applications
                'pending': pending,    # Number of pending applications
                'rejected': rejected   # Number of rejected applications
            },
            'properties': {
                'available': available_properties,  # Currently available properties
                'rented': rented_properties          # Currently rented out
            }
        }
    }, status=200)  # HTTP 200 OK

# Allow only GET requests (fetch dashboard data)
@api_view(['GET'])  # TENANT DASHBOARD
# Ensure only logged-in users can access this endpoint
@permission_classes([IsAuthenticated])
def tenant_dashboard(request):
    # Check if the user is a tenant
    if request.user.user_type != 'tenant':
        # If not a tenant, deny access
        return Response({
            'code': 6001,
            'status': False,
            'message': 'Only tenants can access this dashboard.'
        }, status=403)

    # Get all rental applications submitted by the tenant
    applications = Application.objects.filter(tenant=request.user)
    # Total number of applications submitted
    total_applications = applications.count()
    # Count of approved applications
    approved = applications.filter(status='approved').count()
    # Count of pending applications
    pending = applications.filter(status='pending').count()
    # Count of rejected applications
    rejected = applications.filter(status='rejected').count()

    # Count of unread notifications for this tenant
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    # Total number of notifications for this tenant
    total_notifications = Notification.objects.filter(user=request.user).count()

    # Return the compiled dashboard data in a structured response
    return Response({
        'code': 6000,
        'status': True,
        'message': 'Dashboard data fetched successfully.',
        'data': {
            'total_applications': total_applications,  # Total applications made by tenant
            'applications': {
                'approved': approved,  # Approved applications
                'pending': pending,    # Pending applications
                'rejected': rejected   # Rejected applications
            },
            'notifications': {
                'unread': unread_notifications,  # Notifications not yet read
                'total': total_notifications     # All notifications
            }
        }
    }, status=200)  # Return with HTTP 200 OK status


# Allow only POST requests (to create a new payment)
@api_view(['POST'])
# Ensure the user is authenticated before proceeding
@permission_classes([IsAuthenticated])
def create_payment(request, property_id):
    # Check if the user is a tenant; only tenants can make payments
    if request.user.user_type != 'tenant':
        return Response({
            'code': 6001,
            'status': False,
            'message': 'Only tenants can make payments.'
        }, status=status.HTTP_403_FORBIDDEN)

    # Try to fetch the property using the given property_id
    try:
        property_instance = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        # If property not found, return an error response
        return Response({
            'code': 6002,
            'status': False,
            'message': 'Property not found.'
        }, status=status.HTTP_404_NOT_FOUND)

    # Check if the tenant has an approved application for the property
    try:
        approved_application = Application.objects.get(
            property=property_instance, 
            tenant=request.user, 
            status='approved'
        )
    except Application.DoesNotExist:
        # If not, deny the payment attempt
        return Response({
            'code': 6003,
            'status': False,
            'message': 'You do not have an approved application for this property.'
        }, status=status.HTTP_403_FORBIDDEN)

    # If the property is marked as available, payment shouldn't be allowed
    if property_instance.is_available:
        return Response({
            'code': 6004,
            'status': False,
            'message': 'Property is not available for payment.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Try to retrieve the payment amount from request data and convert to Decimal
    try:
        amount = Decimal(request.data.get('amount'))
    except:
        # If conversion fails or amount is missing, return an error
        return Response({
            'code': 6005,
            'status': False,
            'message': 'Invalid or missing amount.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Create a new Payment object and save it to the database
    payment = Payment.objects.create(
        tenant=request.user,
        property=property_instance,
        amount=amount
    )

    # Return success response with serialized payment data
    return Response({
        'code': 6000,
        'status': True,
        'message': 'Payment initiated successfully.',
        'data': PaymentSerializer(payment).data
    }, status=status.HTTP_201_CREATED)



# This view handles GET requests to list all payments made by a tenant
@api_view(['GET'])
# Ensures only authenticated users can access this view
@permission_classes([IsAuthenticated])
def list_payments(request):
    # Check if the logged-in user is a tenant
    if request.user.user_type != 'tenant':
        return Response({
            'code': 6001,
            'status': False,
            'message': 'Only tenants can view payments.'
        }, status=status.HTTP_403_FORBIDDEN)  # Return forbidden if user is not a tenant

    # Retrieve all payment records made by the tenant
    payments = Payment.objects.filter(tenant=request.user)

    # If no payments found, return an empty list with a success message
    if not payments.exists():
        return Response({
            'code': 6002,
            'status': True,
            'message': 'No payments found for this tenant.',
            'data': []
        }, status=status.HTTP_200_OK)

    # Serialize the list of payments for response
    serializer = PaymentSerializer(payments, many=True)

    # Return the serialized data with a success message
    return Response({
        'code': 6000,
        'status': True,
        'message': 'Payments fetched successfully.',
        'data': serializer.data
    }, status=status.HTTP_200_OK)

# This view allows updating the status of a payment using PATCH method
@api_view(['PATCH'])
# Ensures that only authenticated users can access the view
@permission_classes([IsAuthenticated])
def update_payment_status(request, payment_id):
    # Check if the user is either an owner or admin; others are not allowed
    if request.user.user_type not in ['owner', 'admin']:
        return Response({
            'code': 6001,
            'status': False,
            'message': 'Only owners or admins can update payment status.'
        }, status=status.HTTP_403_FORBIDDEN)  # Return 403 Forbidden if unauthorized

    try:
        # Try to retrieve the Payment object by its ID
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        # If the payment does not exist, return a 404 response
        return Response({
            'code': 6002,
            'status': False,
            'message': 'Payment not found.'
        }, status=status.HTTP_404_NOT_FOUND)

    # Extract the new status value from the request data
    status_value = request.data.get('status')

    # If no status value is provided in the request, return a 400 error
    if not status_value:
        return Response({
            'code': 6003,
            'status': False,
            'message': 'Status value is required.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Update the status of the payment object
    payment.status = status_value
    # Save the updated payment object to the database
    payment.save()

    # Return a success response with the updated payment data
    return Response({
        'code': 6000,
        'status': True,
        'message': 'Payment status updated successfully.',
        'data': PaymentSerializer(payment).data  # Serialize the updated payment object
    }, status=status.HTTP_200_OK)

# Define a POST endpoint to submit a review for a property
@api_view(['POST'])
# Ensure only authenticated users can access this endpoint
@permission_classes([IsAuthenticated])
def submit_review(request, property_id):
    try:
        # Try to get the property instance by its ID
        property_instance = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        # If property does not exist, return a 404 response
        return Response({
            'code': 6001,
            'status': False,
            'message': 'Property not found.'
        }, status=status.HTTP_404_NOT_FOUND)

    # Prepare the data dictionary to pass to the serializer
    data = {
        'property': property_id,                   # ID of the property being reviewed
        'tenant': request.user.id,                 # ID of the currently logged-in user
        'rating': request.data.get('rating'),      # Rating value from the request
        'review': request.data.get('review')       # Review text from the request
    }

    # Pass the data to the ReviewSerializer for validation
    serializer = ReviewSerializer(data=data)

    # If the serializer data is valid, save the review
    if serializer.is_valid():
        # Save the review instance, passing actual objects for tenant and property
        serializer.save(property=property_instance, tenant=request.user)
        return Response({
            'code': 6000,
            'status': True,
            'message': 'Review submitted successfully.',
            'data': serializer.data  # Return the serialized review data
        }, status=status.HTTP_201_CREATED)

    # If the serializer is not valid, return validation errors
    return Response({
        'code': 6002,
        'status': False,
        'message': 'Validation failed.',
        'errors': serializer.errors  # Detailed serializer error messages
    }, status=status.HTTP_400_BAD_REQUEST)


# Define a GET endpoint to list all reviews for a given property
@api_view(['GET'])
def list_reviews(request, property_id):
    try:
        # Try to retrieve the property object with the given ID
        property_instance = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        # If the property doesn't exist, return a 404 error response
        return Response({
            'code': 6001,
            'status': False,
            'message': 'Property not found.'
        }, status=status.HTTP_404_NOT_FOUND)

    # Fetch all reviews associated with this property using the reverse relation
    reviews = property_instance.reviews.all()  # Ensure `related_name='reviews'` is set in the Review model

    # Serialize the review queryset into a list of dictionaries
    serializer = ReviewSerializer(reviews, many=True)

    # Return a success response with the serialized review data
    return Response({
        'code': 6000,
        'status': True,
        'message': 'Reviews fetched successfully.',
        'data': serializer.data
    }, status=status.HTTP_200_OK)

# Define a PATCH endpoint to update a review for a given review_id
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])  # Ensure that only authenticated users can update reviews
def update_review(request, review_id):
    try:
        # Try to retrieve the review object with the given review ID
        review = PropertyReview.objects.get(id=review_id)
    except PropertyReview.DoesNotExist:
        # If the review doesn't exist, return a 404 error response
        return Response({
            'code': 6001,
            'status': False,
            'message': 'Review not found.'
        }, status=status.HTTP_404_NOT_FOUND)

    # Check if the review belongs to the current authenticated tenant
    if review.tenant != request.user:
        # If the authenticated user is not the owner of the review, return a 403 Forbidden error
        return Response({
            'code': 6002,
            'status': False,
            'message': 'You can only update your own review.'
        }, status=status.HTTP_403_FORBIDDEN)

    # Serialize the review data with partial update (only the fields provided in the request data will be updated)
    serializer = ReviewSerializer(review, data=request.data, partial=True)

    if serializer.is_valid():
        # If the serializer data is valid, save the updated review to the database
        serializer.save()
        # Return a success response with the updated review data
        return Response({
            'code': 6000,
            'status': True,
            'message': 'Review updated successfully.',
            'review': serializer.data
        })

    # If the serializer data is not valid, return a 400 Bad Request with the errors
    return Response({
        'code': 6003,
        'status': False,
        'message': 'Invalid data provided.',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# Define a GET endpoint to list all properties that tenants have applied for
@api_view(['GET'])
@permission_classes([AllowAny])  # Allow anyone (including unauthenticated users) to view the applied properties
def list_all_applied_properties(request):
    # Get all applications from the database
    applications = Application.objects.all()

    # Get all properties that are associated with the applications
    applied_properties = Property.objects.filter(id__in=[application.property.id for application in applications])

    # If no applied properties exist, return a 404 error response
    if not applied_properties.exists():
        return Response({
            'code': 6001,
            'status': False,
            'message': 'No applied properties found.'
        }, status=status.HTTP_404_NOT_FOUND)

    # Serialize the applied properties, passing the request context for absolute image URLs
    serializer = PropertySerializer(applied_properties, many=True, context={'request': request})

    # Return a successful response with the serialized applied properties data
    return Response({
        'code': 6000,
        'status': True,
        'message': 'Applied properties retrieved successfully.',
        'properties': serializer.data
    })
# Define a GET endpoint to list properties that have tenants applied
@api_view(['GET'])  # Only GET requests are allowed for this view
@permission_classes([AllowAny])  # Allow any user (authenticated or not) to access this endpoint
def properties_with_applicants(request):
    data = []  # Initialize an empty list to store the properties and their applicants

    # Get all properties that have at least one application (i.e., filter properties with non-null applications)
    properties = Property.objects.filter(applications__isnull=False).distinct()

    # If no properties with applications are found, return a 404 response
    if not properties.exists():
        return Response({
            'code': 6001,
            'status': False,
            'message': 'No properties with applicants found.'
        }, status=status.HTTP_404_NOT_FOUND)

    # Loop through each property and collect the necessary data
    for prop in properties:
        # Get all applications for the current property
        applications = Application.objects.filter(property=prop)
        
        # Extract tenant usernames from the applications
        tenant_names = [app.tenant.username for app in applications]

        # Append a dictionary of property details to the 'data' list
        data.append({
            "property_id": prop.id,
            "property_name": prop.name,  # Assuming the property model has 'name' field
            "owner": prop.user.username if prop.user else None,  # Get the username of the owner (if exists)
            "city": prop.city,  # Assuming the property model has 'city' field
            "state": prop.state,  # Assuming the property model has 'state' field
            "tenants_applied": tenant_names  # List of tenant usernames who applied for the property
        })

    # Return a successful response with the property data
    return Response({
        'code': 6000,
        'status': True,
        'message': 'Properties with applicants retrieved successfully.',
        'properties': data
    })