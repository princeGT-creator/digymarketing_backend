from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import (
    Appellant,
    AppellantFile,
    Address,
    Generation,
    Case
    )
from .serializers import (
    AppellantSerializer,
    AppellantFileSerializer,
    AddressSerializer,
    GenerationSerializer,
    CaseSerializer
    )
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .utils import generate_legal_document
from django.http import JsonResponse
from django.shortcuts import render, redirect
import paypalrestsdk
from .paypal_integration import configure_paypal


class AppellantViewSet(viewsets.ModelViewSet):
    queryset = Appellant.objects.all()
    serializer_class = AppellantSerializer

class AppellantFileViewSet(viewsets.ModelViewSet):
    queryset = AppellantFile.objects.all()
    serializer_class = AppellantFileSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('file')  # Handles multiple files
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
    permission_classes = [IsAuthenticated]  # Requires authentication

    def get_serializer_context(self):
        # print(generate_legal_document(19))
        return {'request': self.request}
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            case = serializer.save()
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

configure_paypal()

class CreatePaymentView(APIView):
    def post(self, request, case_id):
        # Retrieve the case object
        try:
            case = Case.objects.get(id=case_id)
        except Case.DoesNotExist:
            return Response({"error": "Case not found."}, status=status.HTTP_404_NOT_FOUND)

        # Create payment for the case
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
                    "total": str(case.total_payment),  # Total payment amount from the case
                    "currency": "USD"
                },
                "description": f"Payment for case {case.case_no}"
            }]
        })

        # Create the payment
        if payment.create():
            # Redirect user to PayPal for approval
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    return redirect(approval_url)
        else:
            return Response({"error": "Payment creation failed."}, status=status.HTTP_400_BAD_REQUEST)

class ExecutePaymentView(APIView):
    def get(self, request, case_id):
        payment_id = request.GET.get("paymentId")
        payer_id = request.GET.get("PayerID")

        # Find the payment from PayPal
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
        except paypalrestsdk.exceptions.ResourceNotFound as e:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        # Execute payment
        if payment.execute({"payer_id": payer_id}):
            # Payment successful, mark the case as paid
            case = Case.objects.get(id=case_id)
            case.status = "Paid"
            case.save()
            return redirect("payment_success")  # Redirect to success page
        else:
            return Response({"error": "Payment execution failed."}, status=status.HTTP_400_BAD_REQUEST)
        
class CancelPaymentView(APIView):
    def get(self, request):
        # You can show a cancellation message to the user or handle any additional logic
        return Response({"message": "Payment has been canceled by the user."}, status=status.HTTP_400_BAD_REQUEST)