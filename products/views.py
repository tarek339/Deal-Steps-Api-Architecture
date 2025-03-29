from django.http import JsonResponse
import json
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from customer.models import *
from .models import *
from django.core.exceptions import ObjectDoesNotExist


@csrf_exempt
def fetch_products(request):
    if request.method == "GET":
        try:
            products = Product.objects.values()
            return JsonResponse(
                list(products),
                safe=False,
                status=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            return JsonResponse(
                {"error": "No Products found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Catch-all for unexpected errors
            return JsonResponse(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


@csrf_exempt
def fetch_single_product(request, id):
    if request.method == "GET":
        try:
            product = Product.objects.get(id=id)

            return JsonResponse(
                {
                    "product": {
                        "id": product.id,
                        "shopName": product.shopName,
                        "brand": product.brand,
                        "description": product.description,
                        "price": product.price,
                        "imageUrl": product.imageUrl,
                    }
                },
                status=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            return JsonResponse(
                {"error": "No Product with this ID found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            # Catch-all for unexpected errors
            return JsonResponse(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


@csrf_exempt
def add_to_cart(request, id):
    if request.method == "POST":
        body_unicode = request.body.decode("utf-8")
        body_data = json.loads(body_unicode)
        product_id = body_data.get("productId")
        customer_id = get_object_or_404(Customer, id=id)
        product = get_object_or_404(Product, id=product_id)

        cart, created = Cart.objects.get_or_create(customer=customer_id)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        cart_item.quantity += 1
        cart_item.save()

        return JsonResponse(
            {
                "message": "Item added to cart",
            },
            status=status.HTTP_200_OK,
        )

    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


@csrf_exempt
def fetch_cart(request, id):
    if request.method == "GET":
        customer_id = get_object_or_404(Customer, id=id)

        try:
            cart = Cart.objects.get(customer=customer_id)

            if not cart:
                return JsonResponse(
                    {"message": "Cart is empty"},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            cart_data = []

            for item in cart.items.all():
                cart_data.append(
                    {
                        "id": item.product.id,
                        "brand": item.product.brand,
                        "description": item.product.description,
                        "quantity": item.quantity,
                        "totalPrice": item.total,
                        "price": item.product.price,
                    }
                )

            return JsonResponse(
                {"cart": {"cart": cart_data}},
                status=status.HTTP_200_OK,
            )

        except ObjectDoesNotExist:
            return JsonResponse(
                {"error": "No Cart found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Catch-all for unexpected errors
            return JsonResponse(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


@csrf_exempt
def remove_from_cart(request, id):
    if request.method == "POST":
        body_unicode = request.body.decode("utf-8")
        body_data = json.loads(body_unicode)
        product_ids = body_data.get("selectedProducts")

        try:
            customer_id = get_object_or_404(Customer, id=id)
            products = Product.objects.filter(id__in=product_ids)
            cart = Cart.objects.get(customer=customer_id)
            cart_items = CartItem.objects.filter(cart=cart, product__in=products)

            for cart_item in cart_items:
                cart_item.delete()

            return JsonResponse(
                {
                    "message": "Item removed from cart",
                }
            )

        except ObjectDoesNotExist:
            return JsonResponse(
                {"error": "No Cart found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Catch-all for unexpected errors
            return JsonResponse(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return JsonResponse(
            {"Unprocessable entity": "Invalid request method."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
