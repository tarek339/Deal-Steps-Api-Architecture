import json
from django.shortcuts import render
from .models import *
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
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
        try:
            # Parse the request body
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")

            # Create the customer (assuming a Customer model exists)
            customer = Customer.objects.create_user(
                username=email, email=email, password=password
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
                    "customer_id": customer.id,
                    "token": token,
                },
                status=status.HTTP_201_CREATED,
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON format."}, status=status.HTTP_400_BAD_REQUEST
            )
        except IntegrityError:
            return JsonResponse(
                {"error": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return JsonResponse(
                {"error": str(e, "All fields are required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Catch-all for unexpected errors
            return JsonResponse(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method or missing fields."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Verify email
@csrf_exempt
def verify_email(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            verificationToken = data.get("token")

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
        except customer.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid token."},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON format."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return JsonResponse(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method or missing fields."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Sign in customer
@csrf_exempt
def sign_in_customer(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")

        try:
            customer = Customer.objects.get(email=email)
            checked = customer.check_password(password)
            if checked and customer.email is not None:
                # Generate token for locale storage
                expiration_time = datetime.datetime.now(
                    datetime.timezone.utc
                ) + datetime.timedelta(days=7)

                token = jwt.encode(
                    {"exp": expiration_time, "user_id": str(customer.id)},
                    settings.JWT_SECRET_TOKEN,
                    algorithm="HS256",
                )
                return JsonResponse(
                    {
                        "message": "Login successful",
                        "user": {
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
                        "token": token,
                    },
                    status=status.HTTP_200_OK,
                )
            return JsonResponse(
                {"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        except Customer.DoesNotExist:
            return JsonResponse(
                {"message": "Customer with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as e:
            return JsonResponse(
                {"error": str(e, "All fields are required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON format."}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return JsonResponse(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method or missing fields."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Get customer profile
@csrf_exempt
def get_customer_profile(request):
    if request.method == "GET":
        try:
            customer_id = authentication(request)
            if not customer_id:
                return JsonResponse(
                    {"error": "Unauthorized access"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            customer = Customer.objects.get(id=customer_id)
            return JsonResponse(
                {
                    "user": {
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
                status=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            return JsonResponse(
                {"error": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return JsonResponse(
                {"error": f"An error occurred: {str(e)}"},
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
        body_unicode = request.body.decode("utf-8")
        data = json.loads(body_unicode)
        firstName = data.get("firstName")
        lastName = data.get("lastName")
        street = data.get("street")
        houseNumber = data.get("houseNumber")
        zipCode = data.get("zipCode")
        city = data.get("city")

        try:
            customer = Customer.objects.get(id=id)
            if not customer:
                return JsonResponse(
                    {"message": "Customer with this ID does not exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )

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
                    "user": {
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
                status=status.HTTP_200_OK,
            )

        except Customer.DoesNotExist:
            return JsonResponse(
                {"message": "Customer with this ID does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as e:
            return JsonResponse(
                {"error": str(e, "All fields are required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return JsonResponse(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method or missing fields."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Change customer password
@csrf_exempt
def change_constumers_password(request, id):
    if request.method == "PUT":
        body_unicode = request.body.decode("utf-8")
        data = json.loads(body_unicode)
        prev_password = data.get("oldPassword")
        new_password = data.get("newPassword")
        confirm_new_password = data.get("confirmPassword")

        try:
            customer = Customer.objects.get(id=id)
            checked = customer.check_password(prev_password)

            if not prev_password:
                return JsonResponse(
                    {"message": "Password is required"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            if not checked:
                return JsonResponse(
                    {"message": "Passwords must match"},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            if new_password != confirm_new_password:
                return JsonResponse(
                    {"message": "Password is incorrect"},
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
        except ValidationError as e:
            return JsonResponse(
                {"error": str(e, "All fields are required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return JsonResponse(
                {"error": f"An error occurred: {str(e)}"},
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
        body_unicode = request.body.decode("utf-8")
        data = json.loads(body_unicode)
        new_email = data.get("newEmail")
        confirm_email = data.get("confirmEmail")

        try:
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
                "Verify Your Email",
                f"Hi, please verify your email by clicking on the link: {verification_link}",
                settings.DEFAULT_FROM_EMAIL,
                [new_email],
                fail_silently=False,
            )
            return JsonResponse(
                {"message": "Check your inbox to verify the new email"},
                status=status.HTTP_200_OK,
            )

        except Customer.DoesNotExist:
            return JsonResponse(
                {"message": "Customer with this ID does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as e:
            return JsonResponse(
                {"error": str(e, "All fields are required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return JsonResponse(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method or missing fields."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Delete customer
@csrf_exempt
def delete_customer(request, id):
    if request.method == "DELETE":
        try:
            customer = get_object_or_404(Customer, id=id)
            customer.delete()
            return JsonResponse(
                {"message": "profile deleted"}, status=status.HTTP_204_NO_CONTENT
            )
        except ObjectDoesNotExist:
            return JsonResponse(
                {"error": "customer not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return JsonResponse(
                {"error": f"an error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method or missing fields."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
