from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('token/', views.get_visitor_token, name='visitor_token'),
]
