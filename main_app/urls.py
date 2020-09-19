from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/new_user', views.register_user, name='register_user'),
    path('accounts/parent_signup/', views.parent_signup, name='parent_signup'),
    path('accounts/nonparent_signup/', views.nonparent_signup, name='nonparent_signup'),
    path('children/', views.children_index, name='index'),
]