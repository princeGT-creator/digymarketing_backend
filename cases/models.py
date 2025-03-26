from django.db import models
from users.models import TimestampedModel
from .google_drive_service import create_drive_folder
from .google_drive_service import upload_to_drive


MARITAL_STATUS_CHOICES = (
    ('single', 'Single'),
    ('married', 'Married'),
    ('divorced', 'Divorced'),
    ('widow', 'Widow'),
    ('separated', 'Separate/Separate'),
    ('busy', 'Busy'),
)


class Appellant(models.Model):
    name = models.CharField(max_length=30)
    email = models.EmailField()
    is_minor = models.BooleanField(default=False)
    birth_place = models.CharField(max_length=100, null=True, blank=True)
    fical_code = models.CharField(max_length=30)
    dob = models.DateField(null=True, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, null=True, blank=True)
    drive_folder_id = models.CharField(max_length=100, blank=True, null=True)  # Store Drive Folder ID

    def save(self, *args, **kwargs):
        if not self.drive_folder_id:
            self.drive_folder_id = create_drive_folder(self.name)
        super().save(*args, **kwargs)


class AppellantFile(models.Model):
    appellant = models.ForeignKey("Appellant", on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="temp_files/")  # Temporarily store before upload
    drive_file_id = models.CharField(max_length=100, blank=True, null=True)
    drive_file_link = models.URLField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save locally first
        file_path = self.file.path
        file_name = self.file.name
        
        # Upload to the specific Appellant's Google Drive folder
        if self.appellant.drive_folder_id:
            drive_file_id, drive_file_link = upload_to_drive(file_path, file_name, self.appellant.drive_folder_id)
            
            # Update model with Drive details
            self.drive_file_id = drive_file_id
            self.drive_file_link = drive_file_link
            super().save(*args, **kwargs)

            # Delete local file
            if os.path.exists(file_path):
                os.remove(file_path)