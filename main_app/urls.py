from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/new_user', views.register_user, name='register_user'),
    path('accounts/parent_signup/', views.parent_signup, name='parent_signup'),
    path('accounts/nonparent_signup/', views.nonparent_signup, name='nonparent_signup'),
    path('accounts/edit_password/', views.edit_password, name='edit_password'),
    path('children/', views.children_index, name='index'),
    path('children/add', views.add_child, name='add_child'),
    path('children/<int:child_id>/', views.child_detail, name='child_detail'),
    path('children/<int:child_id>/summary/', views.child_summary, name='child_summary'),
    path('children/<int:child_id>/child_edit/', views.child_edit, name='child_edit'),
    path('children/<int:child_id>/add_parent/', views.add_parent, name='add_parent'),
    path('children/<int:child_id>/add_professional/', views.add_professional, name='add_professional'),
    path('children/<int:child_id>/add_picture/', views.add_picture, name='add_picture'),
    path('children/<int:child_id>/report_card/', views.report_card, name='report_card'),
    path('children/<int:child_id>/add_report_card/', views.add_report_card, name='add_report_card'),
    path('children/<int:child_id>/edit_report_card/<int:report_card_id>', views.edit_report_card, name='edit_report_card'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit_name/', views.edit_name, name='edit_name'),
    path('profile/edit_relationship', views.edit_relationship, name='edit_relationship'),
    path('profile/edit_organization', views.edit_organization, name='edit_organization'),
    path('profile/edit_username', views.edit_username, name='edit_username'),
    # Daily Reports
<<<<<<< HEAD
    path('daily_report/<int:child_id>/',views.daily_report_index, name='daily_report_index'),
    path('daily_report/<int:child_id>/<int:daily_report_id>/detail/', views.daily_report_detail, name='daily_report_detail'),
    path('daily_report/<int:child_id>/add/', views.add_daily_report, name='add_daily_report'),
    path('daily_report/<int:child_id>/<int:daily_report_id>/daily_report_edit/', views.daily_report_edit, name='daily_report_edit'),
]
=======
    # path('reports/',views.ReportList.as_view(), name='reports_index'),
    # path('reports/<int:pk>/', views.ReportDetail.as_view(), name='reports_detail'),
    # path('reports/create/', views.ReportCreate.as_view(), name='reports_create'),
    # path('reports/int:pk>/update/', views.ReportUpdate.as_view(), name='reports_update'),
    # path('reports/int:pk>/delete/', views.ReportDelete.as_view(), name='reports_delete'),
    path('goals/<int:child_id>/', views.goals_index, name='goals_index'),
    path('goals/<int:child_id>/add/', views.add_goal, name='add_goal'),
    path('goals/<int:child_id>/<int:goal_id>/detail/', views.goal_detail, name='goal_detail'),
    path('goals/<int:child_id>/<int:goal_id>/goal_edit/', views.goal_edit, name='goal_edit'),
]
>>>>>>> b1d6be206c6319099f442a18f28c74c8631f0052
