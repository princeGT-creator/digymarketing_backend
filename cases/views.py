from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse
import os
from .models import Appellant, AppellantFile, Address, Generation, Case
from .serializers import AppellantSerializer, AppellantFileSerializer, AddressSerializer, GenerationSerializer, CaseSerializer
import random
import string
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .utils import generate_legal_document, get_object_or_none
from django.http import JsonResponse
from django.shortcuts import render, redirect
import paypalrestsdk
from .paypal_integration import configure_paypal
from users.models import CustomUser, UserRoles
from .permissions import CanViewCasePermission, CanCreateCasePermission


class AppellantViewSet(viewsets.ModelViewSet):
    queryset = Appellant.objects.all()
    serializer_class = AppellantSerializer
    permission_classes = [IsAuthenticated, CanViewCasePermission, CanCreateCasePermission]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # No user creation here anymore — handled in CaseViewSet
        appellant = serializer.save()

        output_serializer = self.get_serializer(appellant)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class AppellantFileViewSet(viewsets.ModelViewSet):
    queryset = AppellantFile.objects.all()
    serializer_class = AppellantFileSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, CanViewCasePermission, CanCreateCasePermission]

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('file')
        appellant_id = request.data.get('appellant')

        if not appellant_id:
            return Response({"error": "Appellant ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        created_files = []

        for file in files:
            serializer = self.get_serializer(data={
                'appellant': appellant_id,
                'file': file
            })

            serializer.is_valid(raise_exception=True)
            serializer.save()
            created_files.append(serializer.data)

        return Response(created_files, status=status.HTTP_201_CREATED)


class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticated, CanViewCasePermission, CanCreateCasePermission]

    def get_serializer_context(self):
        return {'request': self.request}

    def get_queryset(self):
        user = self.request.user
        if user.role in ['super_admin', 'admin']:
            return Case.objects.filter(payment_status="COMPLETED")
        elif user.role == "customer":
            return Case.objects.filter(appellants__user=user, payment_status="COMPLETED")
        elif user.role == "external_lawyer":
            return Case.objects.filter(created_by=user)
        return Case.objects.filter(lawyer=user, payment_status="COMPLETED")


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            case = serializer.save()
            appellants = case.appellants.all()

            if appellants.exists():
                first_appellant = appellants.first()

                if not first_appellant.user:
                    # Try to find an existing user by email
                    existing_user = CustomUser.objects.filter(email=first_appellant.email).first()
                    print('existing_user: ', existing_user)

                    if existing_user:
                        # Link existing user to appellant
                        first_appellant.user = existing_user
                        first_appellant.save()

                        # Send email to notify case assignment (no password)
                        subject = "You have been assigned to a new case"
                        message = (
                            f"Hello {existing_user.first_name},\n\n"
                            f"You have been assigned to a new case.\n"
                            f"Email: {existing_user.email}\n"
                            f"Role: {existing_user.role}\n\n"
                            f"You can log in with your existing credentials."
                        )
                    else:
                        # Create a new user and assign it
                        temp_password = "".join(random.choices(string.ascii_letters + string.digits, k=10))
                        user = CustomUser.objects.create_user(
                            email=first_appellant.email,
                            password=temp_password,
                            role=UserRoles.CUSTOMER,
                            first_name=first_appellant.name
                        )
                        first_appellant.user = user
                        first_appellant.save()

                        subject = "Your Case Access Credentials"
                        message = (
                            f"Hello {user.first_name},\n\n"
                            f"You have been assigned to a new case.\n"
                            f"Email: {user.email}\n"
                            f"Role: {user.role}\n"
                            f"Temporary Password: {temp_password}\n\n"
                            f"Please change your password after logging in."
                        )

                    # Send email
                    try:
                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[first_appellant.email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        print(f"Failed to send case email: {e}")

            return Response(CaseSerializer(case).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]


class GenerationViewSet(viewsets.ModelViewSet):
    queryset = Generation.objects.all()
    serializer_class = GenerationSerializer
    permission_classes = [IsAuthenticated]


# configure_paypal()

class CreatePaymentView(APIView):
    def post(self, request, case_id):
        try:
            case = Case.objects.get(id=case_id)
        except Case.DoesNotExist:
            return Response({"error": "Case not found."}, status=status.HTTP_404_NOT_FOUND)

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": f"http://localhost:8000/api/v1/payment/execute/{case_id}/",
                "cancel_url": "http://localhost:8000/api/v1/payment/cancel/"
            },
            "transactions": [{
                "amount": {
                    "total": str(case.total_payment),
                    "currency": "USD"
                },
                "description": f"Payment for case {case.case_no}"
            }]
        })

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    return redirect(link.href)
        return Response({"error": "Payment creation failed."}, status=status.HTTP_400_BAD_REQUEST)


class ExecutePaymentView(APIView):
    def get(self, request, case_id):
        payment_id = request.GET.get("paymentId")
        payer_id = request.GET.get("PayerID")

        try:
            payment = paypalrestsdk.Payment.find(payment_id)
        except paypalrestsdk.exceptions.ResourceNotFound:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        if payment.execute({"payer_id": payer_id}):
            case = Case.objects.get(id=case_id)
            case.status = "Paid"
            case.save()
            return redirect("payment_success")
        return Response({"error": "Payment execution failed."}, status=status.HTTP_400_BAD_REQUEST)


class CancelPaymentView(APIView):
    def get(self, request):
        return Response({"message": "Payment has been canceled by the user."}, status=status.HTTP_400_BAD_REQUEST)


class DownloadLegalDocumentView(APIView):
    def get(self, request, case_id):
        try:
            file_path = generate_legal_document(case_id)
            if os.path.exists(file_path):
                return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CaseRevisionView(APIView):
    def get(self, request, case_id):
        case = get_object_or_none(Case, id=case_id)
        if not case:
            return Response({"error": "Case not found."}, status=status.HTTP_404_NOT_FOUND)

        subject = "Case Revision Requested"
        created_by_name = f"{case.created_by.first_name} {case.created_by.last_name}"
        message = (
            f"Hello {created_by_name},\n\n"
            f"A revision has been requested for your case (ID: {case.id}).\n"
            f"Please review and update the necessary information.\n\n"
            f"Thank you."
        )
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[case.created_by.email],
                fail_silently=False,
            )
            return Response({"message": "Revision email sent successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to send revision email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
