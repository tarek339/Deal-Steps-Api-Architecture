import jwt
from django.conf import settings


def authentication(request):
    token = request.headers.get("Authorization")
    if isinstance(token, str):
        token_data = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = token_data.get("user_id")
        return user_id
