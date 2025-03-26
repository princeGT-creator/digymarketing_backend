from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppellantViewSet, AppellantFileViewSet

router = DefaultRouter()
router.register(r'appellants', AppellantViewSet)
router.register(r'appellant-files', AppellantFileViewSet)

urlpatterns = [
    path('', include(router.urls)),
]