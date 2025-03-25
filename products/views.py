from django.http import JsonResponse
import json
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from customer.models import *
from products.lib.index import *
from .models import *
from django.core.exceptions import ObjectDoesNotExist


def update_products():
    # delete_from_database(Product)
    zalando = scrape_products(
        "https://www.zalando.de/schuhe/",
        "Zalando",
        "article",
        "z5x6ht _0xLoFW JT3_zV mo6ZnF _78xIQ-",
        "h3",
        "FtrEr_ lystZ1 FxZV-M HlZ_Tf ZkIJC- r9BRio qXofat EKabf7",
        "h3",
        "sDq_FX lystZ1 FxZV-M HlZ_Tf ZkIJC- r9BRio qXofat EKabf7",
        "p",
        ["sDq_FX lystZ1 dgII7d HlZ_Tf", "sDq_FX lystZ1 FxZV-M HlZ_Tf"],
    )
    # deichmann_sale = scrape_products(
    #     "https://www.deichmann.com/de-de/herren-schuhe/sneaker/c-mss3",
    #     "Deichmann",
    #     "article",
    #     "m-product-card-entry",
    #     "h4",
    #     "",
    #     "h3",
    #     "",
    #     "strong",
    #     "sale",
    # )
    # deichmann = scrape_products(
    #     "https://www.deichmann.com/de-de/herren-schuhe/sneaker/c-mss3",
    #     "Deichmann",
    #     "article",
    #     "m-product-card-entry",
    #     "h4",
    #     "",
    #     "h3",
    #     "",
    #     "strong",
    #     "",
    # )
    # about_you = scrape_products(
    #     "https://www.aboutyou.de/b/shop/nike-272/all?category=20345&sale=true",
    #     "About You",
    #     "li",
    #     "sc-oelsaz-0 YkKBp",
    #     "p",
    #     "sc-1vt6vwe-0 sc-1vt6vwe-1 sc-1qsfqrd-3 jQLlAg uXZUf iBzidq",
    #     "p",
    #     "sc-1vt6vwe-0 sc-1vt6vwe-1 sc-1qsfqrd-4 jQLlAg uXZUf KJYZl",
    #     "span",
    #     "sc-2qclq4-0 sc-fruv23-0 llOhHy fzbBtI sc-18q4lz4-0 jqbzko",
    # )


# Use pandas for data analysis and matplotlib or seaborn for visualizing the results.
# store the results in a database


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
def fetch_single_product(request, productID):
    if request.method == "GET":
        try:
            product = Product.objects.get(id=productID)
            if not product:
                return JsonResponse(
                    {"error": "Product not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            data = {
                "id": product.id,
                "shopName": product.shopName,
                "brand": product.brand,
                "description": product.description,
                "price": product.price,
                "imageUrl": product.imageUrl,
            }
            return JsonResponse(
                data,
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

        if created:
            cart_item.quantity = 1
        else:
            cart_item.quantity += 1
        cart_item.save()

        return JsonResponse(
            {"message": "Item added to cart"},
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
            total_sum = 0

            for item in cart.items.all():
                item_total_price = item.total
                cart_data.append(
                    {
                        "id": item.product.id,
                        "brand": item.product.brand,
                        "quantity": item.quantity,
                        "totalPrice": item.total,
                    }
                )
                total_sum += item_total_price

            return JsonResponse(
                {"cart": cart_data, "total": total_sum}, status=status.HTTP_200_OK
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
        product_id = body_data.get("productId")
        customer_id = get_object_or_404(Customer, id=id)
        product = get_object_or_404(Product, id=product_id)

        try:
            cart = Cart.objects.get(customer=customer_id)
            cart_item = CartItem.objects.get(cart=cart, product=product)

            if cart_item.quantity > 0:
                cart_item.quantity -= 1
                cart_item.save()

            if cart_item.quantity <= 0:
                cart_item.delete()

            return JsonResponse({"message": "Item removed from cart"})

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
def delete_cart(request, id):
    if request.method == "POST":
        customer_id = get_object_or_404(Customer, id=id)

        try:
            cart = Cart.objects.get(customer=customer_id)
            cart_items = CartItem.objects.filter(cart=cart)

            for item in cart_items:
                item.delete()

            return JsonResponse({"message": "Cart deleted"})

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
