from django.shortcuts import render
from .models import *
from django.http import FileResponse, Http404


def index(request):
    return render(request, 'fram/index.html')

def map(request):
    if not Position.objects.all():
        return render(request, 'fram/map.html', {'positions': 'None'})

    context = {
        'layers': Layer.objects.all().order_by('position__date'),
        }
    return render(request, 'fram/map.html', context)

def daily(request):
    return render(request, 'fram/daily.html', {
        'daily_reports': Daily.objects.all().order_by('-position__date'),
    })

def read_daily(request, dailyID):
    try:
        daily = Daily.objects.get(id=dailyID)
    except Daily.DoesNotExist:
        daily = None

    return render(request, 'fram/read_daily.html', {
        'daily': daily,
    })

def info(request):
    if(request.GET.get('outline')):
        try:
            return FileResponse(open('data/Outline_UiO.pdf', 'rb'), content_type='application/pdf')
        except FileNotFoundError:
            raise Http404()
    if(request.GET.get('project')):
        try:
            return FileResponse(open('data/Prosjektskisse_2019.pdf', 'rb'), content_type='application/pdf')
        except FileNotFoundError:
            raise Http404()
    return render(request, 'fram/info.html')

def weekly(request):
    return render(request, 'fram/weekly.html')

def links(request):
    return render(request, 'fram/links.html')

def contact(request):
    return render(request, 'fram/contact.html')
