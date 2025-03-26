from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, UserRoles, PasswordResetToken
from django.core.mail import send_mail
from django.utils.timezone import now
import random
import string
from django.conf import settings
import os
from dotenv import load_dotenv

load_dotenv() 

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)  # Optional password

    class Meta:
        model = CustomUser
        fields = ["email", "first_name", "last_name", "role", "password"]

    def create(self, validated_data):
        # Generate a random 10-character password (letters + digits)
        dummy_password = "".join(random.choices(string.ascii_letters + string.digits, k=10))

        # Create user with the generated password
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(dummy_password)  # Ensure password hashing
        user.save()

        # Send welcome email with temporary password
        subject = "Your New Account Credentials"
        message = (
            f"Hello {user.first_name},\n\n"
            f"Your account has been created.\n"
            f"Email: {user.email}\n"
            f"Role: {user.role}\n"
            f"Temporary Password: {dummy_password}\n\n"
            f"Please change your password after logging in."
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,  # Use from settings
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {e}")  # Log error (use proper logging in production)

        return user

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ["id", "email", "first_name", "last_name", "role", "password"]

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = CustomUser.objects.get(email=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No user found with this email.")
        
        # Generate a password reset token
        reset_token = PasswordResetToken.create_token(user)

        # Construct the reset URL
        FRONTEND_URL = os.getenv("FRONTEND_URL")
        reset_url = f"{FRONTEND_URL}/reset-password?{reset_token.token}"

        # Send email with the reset link
        send_mail(
            subject="Password Reset Request",
            message=f"Click the link below to reset your password:\n{reset_url}",
            from_email=os.getenv("DEFAULT_FROM_EMAIL"),  # Use your configured email
            recipient_list=[user.email],
            fail_silently=False,
        )
        return value

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            reset_token = PasswordResetToken.objects.get(token=data["token"])
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired token.")

        if reset_token.is_expired():
            reset_token.delete()  # Remove expired token
            raise serializers.ValidationError("Token has expired.")

        data["user"] = reset_token.user  # Store user for password update
        return data

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save()

        # Delete used reset token
        PasswordResetToken.objects.filter(user=user).delete()

class GetMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "email", "first_name", "last_name", "role", "is_active", "is_staff"]