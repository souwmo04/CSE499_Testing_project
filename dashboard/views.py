from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.core.files.base import ContentFile

import pandas as pd
import os
import json
import base64

from .models import Snapshot


# -------------------------
# Landing page
# -------------------------
def landing_page(request):
    return render(request, 'dashboard/landing.html')


# -------------------------
# Dashboard page
# -------------------------
def dashboard_page(request):
    """
    Renders the dashboard page and passes initial CSV data for Chart.js.
    """
    csv_file = os.path.join(settings.BASE_DIR, 'data', 'financial_data.csv')

    if not os.path.exists(csv_file):
        return render(request, 'dashboard/dashboard.html', {
            "chart_data": {}
        })

    df = pd.read_csv(csv_file)

    chart_data = {
        "dates": df['date'].tolist(),
        "gold": df['gold_price'].tolist(),
        "silver": df['silver_price'].tolist(),
        "oil": df['oil_price'].tolist()
    }

    return render(request, 'dashboard/dashboard.html', {
        "chart_data": chart_data
    })


# -------------------------
# API endpoint for live chart updates
# -------------------------
def get_chart_data(request):
    """
    Returns CSV data as JSON so charts auto-refresh.
    """
    csv_file = os.path.join(settings.BASE_DIR, 'data', 'financial_data.csv')

    if not os.path.exists(csv_file):
        return JsonResponse({"error": "CSV file not found"}, status=404)

    df = pd.read_csv(csv_file)

    chart_data = {
        "dates": df['date'].tolist(),
        "gold": df['gold_price'].tolist(),
        "silver": df['silver_price'].tolist(),
        "oil": df['oil_price'].tolist()
    }

    return JsonResponse(chart_data)


# -------------------------
# Dataset Info Page
# -------------------------
def dataset_info_page(request):
    csv_file = os.path.join(settings.BASE_DIR, 'data', 'financial_data.csv')

    if not os.path.exists(csv_file):
        return render(request, 'dashboard/dataset_info.html', {
            'error': f"CSV file not found at {csv_file}"
        })

    df = pd.read_csv(csv_file)

    context = {
        'total_rows': len(df),
        'columns': df.columns.tolist(),
        'sample_rows': df.head(10).to_dict(orient='records')
    }

    return render(request, 'dashboard/dataset_info.html', context)


# -------------------------
# Save Snapshot (from dashboard)
# -------------------------
def save_snapshot(request):
    """
    Saves a dashboard snapshot image + metadata.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    data = json.loads(request.body)
    image_data = data.get('image')

    if not image_data:
        return JsonResponse({'error': 'No image provided'}, status=400)

    # Decode base64 image
    format, imgstr = image_data.split(';base64,')
    ext = format.split('/')[-1]

    image_file = ContentFile(
        base64.b64decode(imgstr),
        name=f'snapshot_{Snapshot.objects.count() + 1}.{ext}'
    )

    # Create snapshot entry
    Snapshot.objects.create(
        title="Dashboard Snapshot",
        image=image_file,
        gold_summary="Gold price captured",
        silver_summary="Silver price captured",
        oil_summary="Oil price captured"
    )

    return JsonResponse({'status': 'success'})


# -------------------------
# Snapshots Page
# -------------------------
def snapshots_page(request):
    """
    Displays REAL snapshots saved from dashboard.
    """
    snapshots = Snapshot.objects.order_by('-created_at')
    return render(request, 'dashboard/snapshots.html', {
        'snapshots': snapshots
    })
