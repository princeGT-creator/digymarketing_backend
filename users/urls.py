from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    LoginView,
    ChangePasswordView,
    ForgotPasswordView,
    ResetPasswordView,
    GetMeView
    )

# Creating a router for the UserViewSet
router = DefaultRouter()
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    # User-related endpoints
    path("", include(router.urls)),  # CRUD operations on users
    
    # Authentication endpoints
    path("login/", LoginView.as_view(), name="login"),  # Login API
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("getme/", GetMeView.as_view(), name="getme"),
]
