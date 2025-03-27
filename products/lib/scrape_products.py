import requests
from bs4 import BeautifulSoup


# Function to scrape product data from a website
def scrape_products(
    url,
    shop_name,
    products_tag,
    products_class,
    description_tag,
    description_class,
    price_tag,
    price_class,
):

    # Send a GET request to the website with headers
    response = requests.get(url)

    # Check if the request was successful
    try:
        response.status_code == 200
        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        product_data = []
        # Update this selector based on the actual HTML structure
        products = soup.find_all(products_tag, class_=products_class)

        # Loop through the products and extract the data
        for product in products:
            shop = shop_name
            description = product.find(description_tag, class_=description_class)
            price = product.find(price_tag, class_=price_class)
            image = product.find("img")

            # Use .text.strip() and handle potential None types
            product_description = description.text.strip() if description else None
            product_price = price.text.strip() if price else None
            image_url = image["src"] if image and "src" in image.attrs else None

            def clean_price(price_str):
                if price_str is not None:
                    cleaned_price_str = "".join(
                        char for char in price_str if char.isdigit() or char == ","
                    )
                    # Replace the comma with a dot for float conversion
                    cleaned_price_str = cleaned_price_str.replace(",", ".")

                else:
                    cleaned_price_str = 0

                # Convert to float and return
                return float(cleaned_price_str)

            floated_product_price = clean_price(product_price)

            # Append data to the product_data list only if product_description and title are found
            if (
                shop
                and product_description
                and floated_product_price
                and floated_product_price > 0
                and image_url
            ):
                product_data.append(
                    {
                        "url": url,
                        "shopName": shop,
                        "description": (
                            product_description.replace('"', "")
                            if product_description.startswith('"')
                            and product_description.endswith('"')
                            else product_description
                        ),
                        "price": floated_product_price,
                        "imageUrl": image_url,
                    }
                )
        return product_data

    except:
        print("Failed to retrieve the webpage. Status code:", response.status_code)
        return None
