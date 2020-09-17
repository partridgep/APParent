from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/new_user', views.register_user, name='register_user'),
    path('accounts/signup/<int:is_parent>', views.signup, name='signup'),
    path('children/', views.children_index, name='index'),
]