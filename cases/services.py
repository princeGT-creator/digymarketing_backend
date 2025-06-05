import random
import string
from django.conf import settings
from django.core.mail import send_mail
from users.models import CustomUser, UserRoles
from .models import Appellant

def create_appellant_with_user(appellant_data):
    password = appellant_data.pop("password", None)
    if not password:
        password = "".join(random.choices(string.ascii_letters + string.digits, k=10))

    user = CustomUser.objects.create_user(
        email=appellant_data["email"],
        password=password,
        role=UserRoles.CUSTOMER,
        first_name=appellant_data.get("name", "")
    )

    appellant = Appellant.objects.create(user=user, **appellant_data)

    # Return password for optional use
    return appellant, password
