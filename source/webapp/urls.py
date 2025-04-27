from django.urls import path
from webapp import views


urlpatterns = [
    # Главная
    path('', views.IndexView.as_view(), name='index'),

    # Отчет
    path('report/<int:report_id>/delete/', views.delete_report, name='delete_report'),

    # Firewall Rules
    path('firewall_rules/', views.FirewallRulesView.as_view(), name='firewall_rules'),
]
