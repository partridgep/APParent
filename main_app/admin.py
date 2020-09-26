from django.contrib import admin
from .models import Profile, Child, Picture, Daily_report, Report_card, Goal, Meeting, Availability_event

# Register your models here.
admin.site.register(Profile)
admin.site.register(Child)
admin.site.register(Picture)
admin.site.register(Daily_report)
admin.site.register(Report_card)
admin.site.register(Goal)
admin.site.register(Meeting)
admin.site.register(Availability_event)
