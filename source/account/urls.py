from django.urls import path
from account import views


urlpatterns = [
    # auth and registration urls
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.logout_view, name='logout'),

# user profile and edit urls
    path('profile/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('profile/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
]
