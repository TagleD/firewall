from django.urls import path
from webapp import views


urlpatterns = [
    # Главная
    path('', views.IndexView.as_view(), name='index'),
]
