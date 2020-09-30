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
    path('children/<int:child_id>/meetings/', views.meetings, name='meetings'),
    path('children/<int:child_id>/add_meeting/', views.add_meeting, name='add_meeting'),
    path('children/<int:child_id>/set_date/<int:teammate_id>/', views.set_date, name='set_date'),
    path('children/<int:child_id>/set_time/<int:teammate_id>/<int:weekday>/<int:month>/<int:month_date>/<int:year>/', views.set_time, name='set_time'),
    path('children/<int:child_id>/create_meeting/<int:teammate_id>/<int:weekday>/<int:month>/<int:month_date>/<int:year>/<int:hour>/<int:minute>/', views.create_meeting, name='create_meeting'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit_name/', views.edit_name, name='edit_name'),
    path('profile/edit_relationship', views.edit_relationship, name='edit_relationship'),
    path('profile/edit_organization', views.edit_organization, name='edit_organization'),
    path('profile/edit_username', views.edit_username, name='edit_username'),
    path('profile/set_availability', views.set_availability, name='set_availability'),
    path('daily_report/<int:child_id>/',views.daily_reports_index, name='daily_reports_index'),
    path('daily_report/<int:child_id>/<int:daily_report_id>/detail/', views.daily_report_detail, name='daily_report_detail'),
    path('daily_report/<int:child_id>/add/', views.add_daily_report, name='add_daily_report'),
    path('daily_report/<int:child_id>/<int:daily_report_id>/daily_report_edit/', views.daily_report_edit, name='daily_report_edit'),
    path('goals/<int:child_id>/', views.goals_index, name='goals_index'),
    path('goals/<int:child_id>/add/', views.add_goal, name='add_goal'),
    path('goals/<int:child_id>/<int:goal_id>/detail/', views.goal_detail, name='goal_detail'),
    path('goals/<int:child_id>/<int:goal_id>/goal_edit/', views.goal_edit, name='goal_edit'),
]
