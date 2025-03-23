from django.urls import path
from account import views

urlpatterns = [
    # auth and registration urls
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.logout_view, name='logout'),

    # user profile and edit urls
    path('profile/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('profile/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_settings'),

    # Export & Share
    path('profile/<int:pk>/export_excel/', views.export_to_excel, name='export_excel'),
    path('profile/<int:pk>/export_csv/', views.export_to_csv, name='export_csv'),
]
