import json
from .models import *
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from customer.authentication.authentication import authentication
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import jwt
import datetime
from django.core.exceptions import ObjectDoesNotExist


# Sign up customer
@csrf_exempt
def sign_up_customer(request):
    if request.method == "POST":
        # Parse the request body
        body_unicode = request.body.decode("utf-8")
        data = json.loads(body_unicode)
        email = data.get("email")
        password = data.get("password")

        if not email:
            return JsonResponse(
                {"message": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not password:
            return JsonResponse(
                {"message": "Password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if Customer.objects.filter(email=email).exists():
                return JsonResponse(
                    {"message": "User with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            new_customer = Customer()

            # Generate email confirmation token
            emailToken = default_token_generator.make_token(new_customer)
            uid = urlsafe_base64_encode(force_bytes(new_customer.pk))

            # Send verification email
            verification_link = (
                f"{settings.FRONTEND_URL}/verify-email?uid={uid}&token={emailToken}"
            )

            new_customer = Customer(
                email=email,
                password=password,
                verificationToken=emailToken,
            )
            new_customer.save()

            send_mail(
                "Verify Your Email",
                f"Hi, please verify your email by clicking on the link: {verification_link}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            # Generate token for locale storage
            expiration_time = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(days=7)

            token = jwt.encode(
                {"exp": expiration_time, "user_id": str(new_customer.id)},
                settings.JWT_SECRET_TOKEN,
                algorithm="HS256",
            )

            # Return success response
            return JsonResponse(
                {
                    "message": "Customer signed up successfully.",
                    "token": token,
                    "customer": {
                        "id": new_customer.id,
                        "email": new_customer.email,
                        "isVerified": new_customer.isVerified,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            # Catch-all for unexpected errors
            return JsonResponse(
                {"message": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Verify email
@csrf_exempt
def verify_email(request):
    if request.method == "POST":
        body_unicode = request.body.decode("utf-8")
        data = json.loads(body_unicode)
        verificationToken = data.get("token")

        try:
            customer = Customer.objects.get(verificationToken=verificationToken)
            customer.isVerified = True
            customer.save()

            return JsonResponse(
                {
                    "message": "new customer verified",
                    "customer": {
                        "id": customer.id,
                        "firstName": customer.firstName,
                        "lastName": customer.lastName,
                        "email": customer.email,
                        "street": customer.street,
                        "houseNumber": customer.houseNumber,
                        "zipCode": customer.zipCode,
                        "city": customer.city,
                        "isVerified": customer.isVerified,
                    },
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as e:
            return JsonResponse(
                {"message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Sign in customer
@csrf_exempt
def sign_in_customer(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")

        if not email:
            return JsonResponse(
                {"message": "Email is required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not password:
            return JsonResponse(
                {"message": "Password is required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            customer = Customer.objects.get(email=email)
            checked = customer.check_password(password)

            if not checked:
                return JsonResponse(
                    {"message": "Password is incorrect"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Generate token for locale storage
            expiration_time = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(days=7)

            token = jwt.encode(
                {"exp": expiration_time, "user_id": str(customer.id)},
                settings.JWT_SECRET_TOKEN,
                algorithm="HS256",
            )

            last_login = datetime.datetime.now()
            customer.last_login = last_login
            customer.save()

            return JsonResponse(
                {
                    "message": "Login successful",
                    "customer": {
                        "id": customer.id,
                        "firstName": customer.firstName,
                        "lastName": customer.lastName,
                        "email": customer.email,
                        "isVerified": customer.isVerified,
                        "address": {
                            "street": customer.street,
                            "houseNumber": customer.houseNumber,
                            "zipCode": customer.zipCode,
                            "city": customer.city,
                        },
                    },
                    "token": token,
                },
                status=status.HTTP_200_OK,
            )

        except Customer.DoesNotExist:
            return JsonResponse(
                {"message": "Customer with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return JsonResponse(
                {"message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Get customer profile
@csrf_exempt
def get_customer_profile(request):
    if request.method == "GET":
        # verfiy if the user is authenticated
        customer_id = authentication(request)
        try:
            customer = Customer.objects.get(id=customer_id)
            return JsonResponse(
                {
                    "customer": {
                        "id": customer.id,
                        "firstName": customer.firstName,
                        "lastName": customer.lastName,
                        "email": customer.email,
                        "address": {
                            "street": customer.street,
                            "houseNumber": customer.houseNumber,
                            "zipCode": customer.zipCode,
                            "city": customer.city,
                        },
                        "isVerified": customer.isVerified,
                    },
                },
                status=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            return JsonResponse(
                {"message": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return JsonResponse(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Edit customer profile
@csrf_exempt
def edit_costumer_profile(request, id):
    if request.method == "PUT":
        # verfiy if the user is authenticated
        customer_id = authentication(request)
        if customer_id is None:
            return JsonResponse(
                {"message": "Unauthorized: Token does not match customer ID."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        body_unicode = request.body.decode("utf-8")
        data = json.loads(body_unicode)
        firstName = data.get("firstName")
        lastName = data.get("lastName")
        street = data.get("street")
        houseNumber = data.get("houseNumber")
        zipCode = data.get("zipCode")
        city = data.get("city")

        if not firstName:
            return JsonResponse(
                {"message": "First name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not lastName:
            return JsonResponse(
                {"message": "Last name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not street:
            return JsonResponse(
                {"message": "Street is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not houseNumber:
            return JsonResponse(
                {"message": "House number is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not zipCode:
            return JsonResponse(
                {"message": "Zip code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not city:
            return JsonResponse(
                {"message": "City is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            customer = Customer.objects.get(id=id)

            customer.firstName = firstName
            customer.lastName = lastName
            customer.street = street
            customer.houseNumber = houseNumber
            customer.zipCode = zipCode
            customer.city = city
            customer.save()

            return JsonResponse(
                {
                    "message": "Customer profile updated",
                    "customer": {
                        "id": customer.id,
                        "firstName": customer.firstName,
                        "lastName": customer.lastName,
                        "email": customer.email,
                        "address": {
                            "street": customer.street,
                            "houseNumber": customer.houseNumber,
                            "zipCode": customer.zipCode,
                            "city": customer.city,
                        },
                        "isVerified": customer.isVerified,
                    },
                },
                status=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            return JsonResponse(
                {"message": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return JsonResponse(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Change customer password
@csrf_exempt
def change_constumers_password(request, id):
    if request.method == "PUT":
        # verfiy if the user is authenticated
        customer_id = authentication(request)
        if customer_id is None:
            return JsonResponse(
                {"message": "Unauthorized: Token does not match customer ID."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        body_unicode = request.body.decode("utf-8")
        data = json.loads(body_unicode)
        prev_password = data.get("password")
        new_password = data.get("newPassword")
        confirm_new_password = data.get("confirmPassword")

        if not prev_password:
            return JsonResponse(
                {"message": "Password is required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not new_password:
            return JsonResponse(
                {"message": "New password is required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not confirm_new_password:
            return JsonResponse(
                {"message": "Confirm password is required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            customer = Customer.objects.get(id=id)
            checked = customer.check_password(prev_password)

            if not checked:
                return JsonResponse(
                    {"message": "Wrong password"},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            if new_password != confirm_new_password:
                return JsonResponse(
                    {"message": "Passwords must match"},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            customer.password = new_password
            customer.save()
            return JsonResponse(
                {"message": "Passwords successfully changed"},
                status=status.HTTP_200_OK,
            )

        except Customer.DoesNotExist:
            return JsonResponse(
                {"message": "Customer with this ID does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return JsonResponse(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method or missing fields."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Change customer email
@csrf_exempt
def change_costumers_email(request, id):
    if request.method == "PUT":
        # verfiy if the user is authenticated
        customer_id = authentication(request)
        if customer_id is None:
            return JsonResponse(
                {"message": "Unauthorized: Token does not match customer ID."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        body_unicode = request.body.decode("utf-8")
        data = json.loads(body_unicode)
        new_email = data.get("email")
        confirm_email = data.get("confirmEmail")

        if not new_email:
            return JsonResponse(
                {"message": "New email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not confirm_email:
            return JsonResponse(
                {"message": "Confirm email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if Customer.objects.filter(email=new_email).exists():
                return JsonResponse(
                    {"message": "User with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            customer = Customer.objects.get(id=id)
            if new_email != confirm_email:
                return JsonResponse(
                    {"message": "E-Mails must match"},
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )

            emailToken = default_token_generator.make_token(customer)
            uid = urlsafe_base64_encode(force_bytes(customer.pk))

            customer.isVerified = False
            customer.verificationToken = emailToken
            customer.email = new_email
            customer.save()

            verification_link = (
                f"{settings.FRONTEND_URL}/verify-email?uid={uid}&token={emailToken}"
            )

            send_mail(
                "Verify Your new email",
                f"Hi, please verify your email by clicking on the link: {verification_link}",
                settings.DEFAULT_FROM_EMAIL,
                [new_email],
                fail_silently=False,
            )
            return JsonResponse(
                {"message": "Check your inbox to verify the new email"},
                status=status.HTTP_200_OK,
            )

        except ObjectDoesNotExist:
            return JsonResponse(
                {"message": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return JsonResponse(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Delete customer
@csrf_exempt
def delete_customer(request, id):
    if request.method == "DELETE":
        # verfiy if the user is authenticated
        customer_id = authentication(request)
        if customer_id is None:
            return JsonResponse(
                {"message": "Unauthorized: Token does not match customer ID."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            customer = get_object_or_404(Customer, id=id)

            # Check if the customer has a cart
            cart = getattr(customer, "cart", None)
            if cart:
                # Delete cart items if they exist
                cart_items = cart.items.all()
                if cart_items.exists():
                    cart_items.delete()
                # Delete the cart itself
                cart.delete()

            # Delete the customer
            send_mail(
                "Thank you for using our service",
                f"Your account has been deleted. Hope to see you again soon.",
                settings.DEFAULT_FROM_EMAIL,
                [customer.email],
                fail_silently=False,
            )
            customer.delete()

            return JsonResponse(
                {"message": "profile deleted"}, status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return JsonResponse(
                {"message": f"an error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
