from django.contrib import admin
from .models import *

admin.site.register(Position)
admin.site.register(Layer)
admin.site.register(Daily)
admin.site.register(Weekly)
admin.site.register(HistoricalDrift)
admin.site.register(InfoPDF)

class CountryFilter(admin.SimpleListFilter):
    title = ('Country')
    parameter_name = 'country'

    def lookups(self, request, model_admin):
        return (
            ('norway', ('From Norway')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'norway':
            return AccessLog.objects.filter(location__contains='Norway')
        else:
            return AccessLog.objects.all()

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'ip', 'location')
    list_filter = (CountryFilter,)
