from django.db import models
from users.models import TimestampedModel, CustomUser
# from .google_drive_service import create_drive_folder
from .google_drive_service import upload_to_drive
import datetime
from django.db.models import Max
import os
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv

load_dotenv() 


MARITAL_STATUS_CHOICES = (
    ('single', 'Single'),
    ('married', 'Married'),
    ('divorced', 'Divorced'),
    ('widow', 'Widow'),
    ('separated', 'Separate'),
    ('busy', 'Busy'),
    ('engaged', 'Engaged'),
    ('relationship', 'Relationship'),
)
ADDRESS_TYPE = (
    ('marriage', 'Marriage'),
    ('death', 'Death')
)

CASE_STATUS = (
    ('In The Compilation Phase', 'In The Compilation Phase'),
    ('In Process', 'In Process'),
    ('File Sent', 'File Sent'),
    ('File Approved', 'File Approved'),
    ('File Filed With The Court', 'File Filed With The Court'),
    ('Assignment And Role Number', 'Assignment And Role Number'),
    ('Court', 'Court'),
    ('Hearing Date', 'Hearing date'),
    ('Sentence', 'Sentence'),
    ('Transcript Of Proceedings (Municipality)', 'Transcript Of Proceedings (Municipality)')
)


class Appellant(models.Model):
    name = models.CharField(max_length=30)
    email = models.EmailField()
    is_minor = models.BooleanField(default=False)
    birth_place = models.CharField(max_length=100, null=True, blank=True)
    fical_code = models.CharField(max_length=30)
    dob = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, null=True, blank=True)
    drive_folder_id = models.CharField(max_length=100, blank=True, null=True)  # Store Drive Folder ID

    def save(self, *args, **kwargs):
        # if not self.drive_folder_id:
        #     if settings.ENVIRONMENT != 'dev':
                # self.drive_folder_id = create_drive_folder(self.name)
        super().save(*args, **kwargs)


class AppellantFile(models.Model):
    appellant = models.ForeignKey("Appellant", on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="temp_files/")  # Temporarily store before upload
    drive_file_id = models.CharField(max_length=100, blank=True, null=True)
    drive_file_link = models.URLField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # First save to generate file path
        is_new = self._state.adding
        super().save(*args, **kwargs)

        # Only handle upload logic when newly created (is_new)
        if is_new:
            # Upload the file to Google Drive regardless of the environment
            drive_file_id, drive_link = upload_to_drive(
                self.appellant.drive_folder_id,  # Appellant's Google Drive folder ID
                self.file.path,  # Local file path
                self.file.name  # The name of the file
            )

            # Update model fields with the file info from Google Drive
            self.drive_file_id = drive_file_id
            self.drive_file_link = drive_link

            # Save the updates with Google Drive information
            super().save(update_fields=["drive_file_id", "drive_file_link"])


class Address(TimestampedModel):
    line = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=100, blank=True, null=True)
    village = models.CharField(max_length=100, blank=True, null=True)
    ad_type = models.CharField(max_length=50, choices=ADDRESS_TYPE, null=True, blank=True)

    
class Case(TimestampedModel):
    court_no = models.CharField(max_length=100)
    case_no = models.CharField(max_length=100, blank=True, null=True, unique=True)
    appellants = models.ManyToManyField(Appellant, related_name="cases")  # M2M Relationship
    lawyer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="cases", null=True, blank=True)
    descendant = models.CharField(max_length=100, blank=True, null=True)
    des_birth_place = models.CharField(max_length=100, blank=True, null=True)
    des_birth_dod = models.DateField(null=True, blank=True)
    married_to = models.CharField(max_length=100, blank=True, null=True)
    marriage_date = models.DateField(null=True, blank=True)
    spouse_citizenship = models.CharField(max_length=100, blank=True, null=True)
    marriage_place = models.ForeignKey(Address, on_delete=models.SET_NULL, related_name="marriage_address", null=True, blank=True)
    grand_parents_dod = models.DateField(null=True, blank=True)
    grand_parents_dop = models.ForeignKey(Address, on_delete=models.SET_NULL, related_name="death_address", null=True, blank=True)
    clause_1 = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=50, choices=CASE_STATUS, default="")  # FIXED CHOICES
    # generation = models.ForeignKey(Generation, on_delete=models.SET_NULL, related_name="case_generations", null=True, blank=True)
    is_consolare = models.BooleanField(default=False)
    is_judicial = models.BooleanField(default=False)
    clause_2 = models.CharField(max_length=100, null=True, blank=True)
    clause_3 = models.CharField(max_length=100, null=True, blank=True)
    clause_4 = models.CharField(max_length=100, null=True, blank=True)
    total_payment = models.DecimalField(max_digits=10, decimal_places=2)
    payment_place = models.CharField(max_length=100, null=True, blank=True)
    date_of_payment = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_cases')

    def calculate_total_payment(self):
        # Assuming you are passing the list of appellant IDs as part of the payload
        appellant_ids = self.appellants.all()  # This would already be a queryset from the DB

        minors = 0
        adults = 0

        # Loop through the appellant IDs and check their 'is_minor' field
        for appellant_id in appellant_ids:
            appellant = get_object_or_404(Appellant, id=appellant_id.id)
            if appellant.is_minor:
                minors += 1
            else:
                adults += 1
        # Total people calculation
        total_people = minors + adults

        # Base amount based on the total number of people
        if total_people == 1:
            base_amount = 2500
        elif total_people == 2:
            base_amount = 2500
        elif total_people == 3:
            base_amount = 3000
        elif total_people == 4:
            base_amount = 3500
        elif total_people == 5:
            base_amount = 4000
        elif total_people == 6:
            base_amount = 4500
        elif total_people == 7:
            base_amount = 5000
        elif total_people == 8:
            base_amount = 5500
        elif total_people == 9:
            base_amount = 6000
        elif total_people == 10:
            base_amount = 6500
        elif total_people == 11:
            base_amount = 7000
        elif total_people == 12:
            base_amount = 7500
        else:
            base_amount = 7500  # For more than 12 people, fallback to 7500
        
        # Debugging output for base amount

        # Calculate additional costs
        extra_for_adults = adults * 600  # For each adult
        registration_fee = 200
        registration_number_fee = total_people * 350 if total_people < 7 else 500 * total_people
        hearing_expenses = 350
        fiscal_stamp = 27

        # Calculate total payment
        total_payment = base_amount + extra_for_adults + registration_fee + registration_number_fee + hearing_expenses + fiscal_stamp

        # Debug output for total payment

        return total_payment

    def generate_case_no(self):
        current_year = datetime.datetime.now().year
        year_prefix = f"A-{str(current_year)[2:4]}-"  # For example, 'A-25-'

        # Find the latest case_no for the current year
        last_case = Case.objects.filter(case_no__startswith=year_prefix).aggregate(Max('case_no'))
        last_case_no = last_case['case_no__max']

        if last_case_no:
            # Extract the number part from the case_no
            last_number = int(last_case_no.split('-')[-1])
            # If the number reaches 9999, increment the year and reset number to 0000
            if last_number == 9999:
                new_case_no = f"{year_prefix}{str(last_number + 1).zfill(4)}"  # A-26-0000
            else:
                new_case_no = f"{year_prefix}{str(last_number + 1).zfill(4)}"  # Increment number
        else:
            # If no case exists for the year, start at 0001
            new_case_no = f"{year_prefix}0001"

        return new_case_no

    def save(self, *args, **kwargs):
        if not self.case_no:
            self.case_no = self.generate_case_no()  # Generate case number before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return self.court_no



class Generation(TimestampedModel):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="generations")
    number = models.PositiveIntegerField(null=True, blank=True)
    desc = models.TextField(null=True, blank=True)