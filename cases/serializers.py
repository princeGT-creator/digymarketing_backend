from rest_framework import serializers
from .models import (
    Appellant,
    AppellantFile,
    Address,
    Generation,
    Case,
    )
from users.models import (
    CustomUser,
    UserRoles
    )
from users.serializers import UserSerializer



class AppellantFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppellantFile
        fields = ['id', 'appellant', 'file', 'drive_file_link', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class AppellantSerializer(serializers.ModelSerializer):
    files = AppellantFileSerializer(many=True, read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Appellant
        fields = [
            'id', 'name', 'email', 'is_minor', 'birth_place',
            'fical_code', 'dob', 'marital_status', 'address',
            'drive_folder_id', 'files', 'password', 'user'
        ]

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"


class GenerationSerializer(serializers.ModelSerializer):
    case = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Generation
        fields = "__all__"


class CaseSerializer(serializers.ModelSerializer):
    appellants = serializers.PrimaryKeyRelatedField(queryset=Appellant.objects.all(), many=True)
    lawyer = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), allow_null=True)

    marriage_place = AddressSerializer(required=False)
    grand_parents_dop = AddressSerializer(required=False)
    generations = GenerationSerializer(many=True, required=False)  # ✅ renamed to `generations`
    created_by = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), required=False)

    class Meta:
        model = Case
        fields = "__all__"

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user

        appellants_data = validated_data.pop('appellants', [])
        marriage_place_data = validated_data.pop('marriage_place', None)
        grand_parents_dop_data = validated_data.pop('grand_parents_dop', None)
        generations_data = validated_data.pop('generations', [])

        if marriage_place_data:
            marriage_place = Address.objects.create(**marriage_place_data)
            validated_data['marriage_place'] = marriage_place

        if grand_parents_dop_data:
            grand_parents_dop = Address.objects.create(**grand_parents_dop_data)
            validated_data['grand_parents_dop'] = grand_parents_dop

        # Create Case
        case = Case.objects.create(**validated_data)

        # Set ManyToMany
        case.appellants.set(appellants_data)
        case.total_payment = case.calculate_total_payment()
        case.save()

        # Create related generations
        for gen_data in generations_data:
            Generation.objects.create(case=case, **gen_data)

        return case

    def update(self, instance, validated_data):
        appellants_data = validated_data.pop('appellants', None)
        marriage_place_data = validated_data.pop('marriage_place', None)
        grand_parents_dop_data = validated_data.pop('grand_parents_dop', None)
        generations_data = validated_data.pop('generations', None)

        if marriage_place_data:
            if instance.marriage_place:
                for key, value in marriage_place_data.items():
                    setattr(instance.marriage_place, key, value)
                instance.marriage_place.save()
            else:
                instance.marriage_place = Address.objects.create(**marriage_place_data)

        if grand_parents_dop_data:
            if instance.grand_parents_dop:
                for key, value in grand_parents_dop_data.items():
                    setattr(instance.grand_parents_dop, key, value)
                instance.grand_parents_dop.save()
            else:
                instance.grand_parents_dop = Address.objects.create(**grand_parents_dop_data)

        # Handle generations: delete old ones and recreate
        if generations_data is not None:
            instance.generations.all().delete()
            for gen_data in generations_data:
                Generation.objects.create(case=instance, **gen_data)

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        if appellants_data is not None:
            instance.appellants.set(appellants_data)
        instance.total_payment = instance.calculate_total_payment()
        instance.save()

        return instance

    def to_representation(self, instance):
        """Customize the representation of CaseSerializer"""
        data = super().to_representation(instance)
        
        # Convert appellants from IDs to serialized objects
        data['appellants'] = AppellantSerializer(instance.appellants.all(), many=True).data
        
        # Convert lawyer from ID to serialized object
        if instance.lawyer:
            data['lawyer'] = UserSerializer(instance.lawyer).data
        
        # Convert created_by from ID to serialized object
        if instance.created_by:
            data['created_by'] = UserSerializer(instance.created_by).data

        return data