from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Appellant, AppellantFile
from .serializers import AppellantSerializer, AppellantFileSerializer

class AppellantViewSet(viewsets.ModelViewSet):
    queryset = Appellant.objects.all()
    serializer_class = AppellantSerializer

class AppellantFileViewSet(viewsets.ModelViewSet):
    queryset = AppellantFile.objects.all()
    serializer_class = AppellantFileSerializer
    parser_classes = (MultiPartParser, FormParser)  # Allows file upload

    def perform_create(self, serializer):
        serializer.save()
