import jwt
from django.conf import settings
from rest_framework import status


def authentication(request):
    token = request.headers.get("Authorization")
    if isinstance(token, str):
        token_data = jwt.decode(token, settings.JWT_SECRET_TOKEN, algorithms=["HS256"])
        user_id = token_data.get("user_id")
        return user_id
