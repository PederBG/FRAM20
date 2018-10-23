from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('letters', views.letters, name='letters'),
    path('info', views.info, name='info'),
    path('letters/<int:letterID>', views.read_letter, name='read_letter'),
]
