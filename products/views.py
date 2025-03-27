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
    clevertronic = scrape_products(
        "https://www.clevertronic.de/kaufen/handy-kaufen?_gl=1*1j2zqgp*_up*MQ..*_gs*MQ..&gclid=Cj0KCQjwy46_BhDOARIsAIvmcwPJz38j7niycvkvlvRCfqQ7s5dPR4QfQJ9qDU0EvrY383n9D1kk7U8aAoeDEALw_wcB",
        "clevertronic",
        "div",
        "product_box js_product_box",
        "a",
        "js_target_link",
        "span",
        "product_price",
    )
    smartphoneonly = scrape_products(
        "https://www.smartphoneonly.de/Handy-ohne-Vertrag",
        "smartphoneonly",
        "div",
        "productbox-inner",
        "a",
        "text-clamp-2",
        "div",
        "productbox-price",
    )
    otto = scrape_products(
        "https://www.otto.de/suche/handys%20angebote/#ech=29050374",
        "otto",
        "article",
        "product spa js_deal_data js_find_colorChange",
        "p",
        "find_tile__name pl_copy100",
        "span",
        "find_tile__retailPrice pl_headline50 find_tile__priceValue find_tile__priceValue--red",
    )
    otto2 = scrape_products(
        "https://www.otto.de/suche/handys%20angebote/#ech=29050374",
        "otto",
        "article",
        "product js_find_colorChange",
        "p",
        "find_tile__name pl_copy100",
        "span",
        "find_tile__retailPrice pl_headline50 find_tile__priceValue find_tile__priceValue--red",
    )
    otto3 = scrape_products(
        "https://www.otto.de/suche/handys%20angebote/#ech=29050374",
        "otto",
        "article",
        "product spa js_deal_data js_find_colorChange",
        "p",
        "find_tile__name pl_copy100",
        "span",
        "find_tile__retailPrice pl_headline50 find_tile__priceValue find_tile__priceValue--red",
    )
    alternate = scrape_products(
        "https://www.alternate.de/Smartphone/Apple-Smartphones",
        "alternate",
        "a",
        "card align-content-center productBox boxCounter campaign-timer-container",
        "div",
        "product-name font-weight-bold",
        "span",
        "price",
    )
    klarmobil = scrape_products(
        "https://www.klarmobil.de/handy-kaufen/",
        "klarmobil",
        "div",
        "bg-white rounded-16 shadow-mobile lg:shadow-desktop transition-shadow overflow-hidden w-full max-w-328 xl:max-w-[392px] hover:shadow-desktop lg:hover:shadow-hover",
        "span",
        "text-black-100 text-center has-exception text-headline-6 default no-hyphens",
        "span",
        "text-16 leading-16 2xs:text-28 2xs:leading-28",
    )

    products = (
        clevertronic + smartphoneonly + otto + otto2 + otto3 + alternate + klarmobil
    )
    for product in products:
        Product.objects.update_or_create(
            shopName=product["shopName"],
            description=product["description"],
            brand=product["description"].split()[0],
            price=product["price"],
            imageUrl=product["imageUrl"],
        )
    # Product.objects.all().delete()


update_products()


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
