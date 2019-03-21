from django.contrib import admin

from .models import *

admin.site.register(Position)
admin.site.register(Layer)
admin.site.register(Daily)
admin.site.register(Weekly)
admin.site.register(HistoricalDrift)
admin.site.register(AccessLog)
admin.site.register(InfoPDF)
