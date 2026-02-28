"""
Core App URL Configuration
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Landing
    path('',                views.home,               name='home'),

    # Auth
    path('register/',       views.register_view,      name='register'),
    path('login/',          views.login_view,          name='login'),
    path('logout/',         views.logout_view,         name='logout'),

    # Studio & Result
    path('studio/',         views.studio_view,         name='studio'),
    path('studio/<int:job_id>/editor/',    views.editor_view,        name='editor'),
    path('studio/<int:job_id>/preview/',   views.preview_colors_api, name='preview_colors'),
    path('studio/<int:job_id>/vectorize/', views.vectorize_action,   name='vectorize_action'),
    path('result/<int:job_id>/',           views.result_view,        name='result'),
    path('download/<int:job_id>/',         views.download_view,      name='download'),

    # Top-Up
    path('topup/',          views.topup_view,          name='topup'),
    path('topup/confirm/',  views.topup_confirm_view,  name='topup_confirm'),

    # History
    path('history/',        views.history_view,        name='history'),
]
