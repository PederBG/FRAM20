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
    return render(request, 'fram/info.html')

def weekly(request):
    if request.GET:
        try: # Using as_attachment because phones/tablets get errors reading pdf in browser. TODO: fix this
            return FileResponse(open('data/weekly/' + request.GET.get('name'), 'rb'), content_type='application/pdf', as_attachment=True)
        except FileNotFoundError:
            raise Http404()

    context = {
        'weeklys': Weekly.objects.all().order_by('-id')
    }

    return render(request, 'fram/weekly.html', context)

def links(request):
    return render(request, 'fram/links.html')

def contact(request):
    return render(request, 'fram/contact.html')
