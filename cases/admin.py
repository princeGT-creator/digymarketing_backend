from django.contrib import admin
from .models import (
    Appellant,
    AppellantFile,
    Case,
    Address,
    Generation
    )

# Register your models here.
admin.site.register(Appellant)
admin.site.register(AppellantFile)
admin.site.register(Case)
admin.site.register(Address)
admin.site.register(Generation)