from django.urls import path
from . import views

urlpatterns = [
    # Landing page
    path('', views.landing_page, name='landing'),

    # Dashboard page
    path('dashboard/', views.dashboard_page, name='dashboard'),

    # Live API endpoint for chart data (used by chart_manager.js)
    path('dashboard/api/chart-data/', views.get_chart_data, name='chart_data_api'),

    # Snapshots page
    path('snapshots/', views.snapshots_page, name='snapshots'),

    path('dashboard/save-snapshot/', views.save_snapshot, name='save_snapshot'),


    # Dataset info page
    path('dataset/', views.dataset_info_page, name='dataset_info')
]
