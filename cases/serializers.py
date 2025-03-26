from rest_framework import serializers
from .models import Appellant, AppellantFile

class AppellantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appellant
        fields = '__all__'

class AppellantFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppellantFile
        fields = ['id', 'appellant', 'file', 'uploaded_at']
        read_only_fields = ['uploaded_at']
