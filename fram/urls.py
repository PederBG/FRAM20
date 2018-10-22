from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('travelletters', views.letters, name='letters'),
]
