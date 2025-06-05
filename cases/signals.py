from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AppellantFile, Appellant
from .google_drive_service import upload_appellant_file_to_case_drive, upload_existing_appellant_files_to_case
import os

@receiver(post_save, sender=AppellantFile)
def upload_file_to_drive(sender, instance, created, **kwargs):
    if created and instance.appellant.case:
        file_path = instance.file.path
        file_name = os.path.basename(instance.file.name)  # <== FIXED
        case = instance.appellant.case

        file_id, view_link = upload_appellant_file_to_case_drive(case, file_path, file_name)
        if file_id:
            instance.drive_file_id = file_id
            instance.drive_file_link = view_link
            instance.save()
        

@receiver(post_save, sender=Appellant)
def upload_files_when_case_added(sender, instance, **kwargs):
    print('instance.case: ', instance.case)
    if instance.case:
        upload_existing_appellant_files_to_case(instance)