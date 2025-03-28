from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AppellantViewSet,
    AppellantFileViewSet,
    CaseViewSet,
    AddressViewSet,
    GenerationViewSet,
    CreatePaymentView,
    ExecutePaymentView,
    CancelPaymentView
    )

router = DefaultRouter()
router.register(r'appellants', AppellantViewSet)
router.register(r'appellant-files', AppellantFileViewSet)
router.register(r'cases', CaseViewSet)
router.register(r'addresses', AddressViewSet)
router.register(r'generations', GenerationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('payment/create/<int:case_id>/', CreatePaymentView.as_view(), name='create_payment'),
    path('payment/execute/<int:case_id>/', ExecutePaymentView.as_view(), name='execute_payment'),
    path('payment/cancel/', CancelPaymentView.as_view(), name='cancel_payment')
]