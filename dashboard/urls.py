from django.urls import path
from . import views

urlpatterns = [
    # Landing page
    path('', views.landing_page, name='landing'),

    # Dashboard page
    path('dashboard/', views.dashboard_page, name='dashboard'),

    # Live API endpoint for chart data (used by chart_manager.js)
    path('dashboard/api/chart-data/', views.get_chart_data, name='chart_data_api'),

    # Snapshots page and save endpoint
    path('snapshots/', views.snapshots_page, name='snapshots'),
    path('dashboard/save-snapshot/', views.save_snapshot, name='save_snapshot'),

    # Dataset info page
    path('dataset/', views.dataset_info_page, name='dataset_info'),

    # =======================================================================
    # VLM (Vision-Language Model) API Endpoints
    # =======================================================================

    # Check VLM (Ollama/LLaVA) status
    path('vlm/status/', views.vlm_status, name='vlm_status'),

    # Chat with AI about the dashboard (uses latest snapshot)
    path('vlm/chat/', views.vlm_chat, name='vlm_chat'),

    # Perform detailed analysis on a snapshot
    path('vlm/analyze/', views.vlm_analyze, name='vlm_analyze'),

    # Regenerate AI summary for a snapshot
    path('vlm/regenerate-summary/', views.vlm_regenerate_summary, name='vlm_regenerate_summary'),
]
