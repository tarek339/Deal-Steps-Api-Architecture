from ..models import Product


def store_in_db(scrape):
    for item in scrape:
        # Extract the product details from the item
        shopName = item.get("shopName")
        brand = item.get("brand")
        name = item.get("name")
        price = item.get("price")
        image_url = item.get("imageUrl")

        # Create a new Product instance
        product = Product(
            shopName=shopName, brand=brand, name=name, price=price, imageUrl=image_url
        )

        # Save the Product instance to the database
        product.save()
