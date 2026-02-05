"""
Dashboard Views - AI-Powered Financial Analytics
=================================================

This module contains all view functions for the Dynamic Dashboard AI application.

Key Features:
- Landing page with modern 3D design
- Dashboard with real-time chart updates
- Snapshot management with AI analysis
- VLM integration for visual question answering

Algorithm: Visual-Time-Series Reasoning Pipeline
-------------------------------------------------
1. Input: User question (text) + latest dashboard snapshot (image)
2. Image Processing: Resize & normalize snapshot for VLM
3. Prompt Construction: Combine question + visual context + reasoning instructions
4. VLM Execution: Send prompt + image to Ollama (LLaVA), receive response
5. Post-Processing: Extract insights (trends, correlations, volatility)
6. Chat Response: Return clear, human-readable answer
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

import pandas as pd
import os
import json
import base64
import logging

from .models import Snapshot

# Import VLM integration modules
import sys
sys.path.insert(0, os.path.join(settings.BASE_DIR, 'vlm_integration'))

logger = logging.getLogger(__name__)


# =========================================================================
# LANDING PAGE
# =========================================================================
def landing_page(request):
    """
    Render the landing page with modern 3D glassmorphism design.
    """
    return render(request, 'dashboard/landing.html')


# =========================================================================
# DASHBOARD PAGE
# =========================================================================
def dashboard_page(request):
    """
    Render the main dashboard with financial charts and KPI cards.

    Data is loaded from the CSV file and passed to the template for
    Chart.js visualization.
    """
    csv_file = os.path.join(settings.BASE_DIR, 'data', 'financial_data.csv')

    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        return render(request, 'dashboard/dashboard.html', {
            'error': 'Financial data file not found',
            'chart_data': {'dates': [], 'gold': [], 'silver': [], 'oil': []},
            'kpi': {}
        })
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return render(request, 'dashboard/dashboard.html', {
            'error': f'Error loading data: {str(e)}',
            'chart_data': {'dates': [], 'gold': [], 'silver': [], 'oil': []},
            'kpi': {}
        })

    # Chart data for all commodities
    chart_data = {
        "dates": df['date'].tolist(),
        "gold": df['gold_price'].tolist(),
        "silver": df['silver_price'].tolist(),
        "oil": df['oil_price'].tolist()
    }

    # Latest values for KPI cards
    latest_row = df.iloc[-1]
    kpi_data = {
        "gold_latest": float(latest_row['gold_price']),
        "silver_latest": float(latest_row['silver_price']),
        "oil_latest": float(latest_row['oil_price']),
        "last_date": latest_row['date']
    }

    latest_snapshot = Snapshot.objects.order_by('-created_at').first()
    latest_snapshot_url = None
    latest_snapshot_created = None
    latest_snapshot_id = None

    if latest_snapshot and latest_snapshot.image:
        latest_snapshot_url = latest_snapshot.image.url
        latest_snapshot_created = latest_snapshot.created_at
        latest_snapshot_id = latest_snapshot.id

    return render(
        request,
        'dashboard/dashboard.html',
        {
            "chart_data": chart_data,
            "kpi": kpi_data,
            "latest_snapshot_url": latest_snapshot_url,
            "latest_snapshot_created": latest_snapshot_created,
            "latest_snapshot_id": latest_snapshot_id
        }
    )


# =========================================================================
# CHART DATA API
# =========================================================================
def get_chart_data(request):
    """
    API endpoint for live chart updates.

    Returns CSV data as JSON for dynamic chart refresh.
    """
    csv_file = os.path.join(settings.BASE_DIR, 'data', 'financial_data.csv')

    if not os.path.exists(csv_file):
        return JsonResponse({"error": "CSV file not found"}, status=404)

    try:
        df = pd.read_csv(csv_file)
        chart_data = {
            "dates": df['date'].tolist(),
            "gold": df['gold_price'].tolist(),
            "silver": df['silver_price'].tolist(),
            "oil": df['oil_price'].tolist()
        }
        return JsonResponse(chart_data)
    except Exception as e:
        logger.error(f"Error in get_chart_data: {e}")
        return JsonResponse({"error": str(e)}, status=500)


# =========================================================================
# DATASET INFO PAGE
# =========================================================================
def dataset_info_page(request):
    """
    Display information about the loaded CSV dataset.
    """
    csv_file = os.path.join(settings.BASE_DIR, 'data', 'financial_data.csv')

    if not os.path.exists(csv_file):
        return render(request, 'dashboard/dataset_info.html', {
            'error': f"CSV file not found at {csv_file}"
        })

    try:
        df = pd.read_csv(csv_file)
        context = {
            'total_rows': len(df),
            'columns': df.columns.tolist(),
            'sample_rows': df.head(10).to_dict(orient='records'),
            'date_range': {
                'start': df['date'].iloc[0] if len(df) > 0 else 'N/A',
                'end': df['date'].iloc[-1] if len(df) > 0 else 'N/A'
            }
        }
        return render(request, 'dashboard/dataset_info.html', context)
    except Exception as e:
        return render(request, 'dashboard/dataset_info.html', {
            'error': f"Error reading CSV: {str(e)}"
        })


# =========================================================================
# SAVE SNAPSHOT
# =========================================================================
@csrf_exempt
@require_http_methods(["POST"])
def save_snapshot(request):
    """
    Save a dashboard snapshot image with optional AI analysis.

    Receives base64-encoded image data from the frontend,
    decodes it, saves to the database, and optionally triggers
    VLM analysis for automatic summary generation.
    """
    try:
        data = json.loads(request.body)
        image_data = data.get('image')

        if not image_data:
            return JsonResponse({'error': 'No image provided'}, status=400)

        # Decode base64 image
        if ';base64,' in image_data:
            format_part, imgstr = image_data.split(';base64,')
            ext = format_part.split('/')[-1]
        else:
            imgstr = image_data
            ext = 'png'

        # Generate unique filename
        import time
        timestamp = int(time.time() * 1000)
        filename = f'snapshot_{timestamp}.{ext}'

        image_file = ContentFile(
            base64.b64decode(imgstr),
            name=filename
        )

        # Create snapshot entry
        snapshot = Snapshot.objects.create(
            title=f"Dashboard Snapshot - {timestamp}",
            image=image_file,
        )

        # Try to generate AI summary asynchronously (don't block the response)
        try:
            generate_ai_summary_for_snapshot(snapshot)
        except Exception as e:
            logger.warning(f"AI summary generation failed: {e}")
            snapshot.ai_analysis_error = str(e)
            snapshot.save()

        return JsonResponse({
            'status': 'success',
            'snapshot_id': snapshot.id,
            'image_url': snapshot.image.url,
            'created_at': timezone.localtime(snapshot.created_at).isoformat(),
            'message': 'Snapshot saved successfully'
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.exception("Error saving snapshot")
        return JsonResponse({'error': str(e)}, status=500)


def generate_ai_summary_for_snapshot(snapshot):
    """
    Generate an AI summary for a snapshot using VLM.

    This function implements the Visual-Time-Series Reasoning Pipeline
    for automatic snapshot description.
    """
    try:
        from vlm_integration.vlm_client import get_vlm_client

        client = get_vlm_client()
        image_path = snapshot.image.path

        result = client.generate_snapshot_summary(image_path)

        if result.get('success'):
            snapshot.ai_summary = result.get('response', '')
            snapshot.ai_analyzed = True
            snapshot.ai_analysis_error = ''
        else:
            snapshot.ai_analyzed = True
            snapshot.ai_analysis_error = result.get('error', 'Unknown error')

        snapshot.save()

    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        snapshot.ai_analysis_error = str(e)
        snapshot.save()


# =========================================================================
# SNAPSHOTS PAGE
# =========================================================================
def snapshots_page(request):
    """
    Display all saved dashboard snapshots with AI summaries.
    """
    snapshots = Snapshot.objects.all().order_by('-created_at')

    # Prepare snapshot data with proper image URLs
    snapshot_list = []
    for snapshot in snapshots:
        snapshot_data = {
            'id': snapshot.id,
            'title': snapshot.title,
            'created_at': snapshot.created_at,
            'image_url': snapshot.image.url if snapshot.image else None,
            'ai_summary': snapshot.ai_summary,
            'ai_analyzed': snapshot.ai_analyzed,
            'has_ai_summary': snapshot.has_ai_summary(),
            'gold_summary': snapshot.gold_summary,
            'silver_summary': snapshot.silver_summary,
            'oil_summary': snapshot.oil_summary,
        }
        snapshot_list.append(snapshot_data)

    return render(request, 'dashboard/snapshots.html', {
        'snapshots': snapshot_list,
        'total_count': len(snapshot_list)
    })


# =========================================================================
# VLM API ENDPOINTS
# =========================================================================

@require_http_methods(["GET"])
def vlm_status(request):
    """
    Check the status of the VLM (Ollama/LLaVA) service.

    Returns:
        JSON with status information about Ollama availability
    """
    try:
        from vlm_integration.vlm_client import get_vlm_client

        client = get_vlm_client()
        available, message = client.is_available()

        return JsonResponse({
            'status': 'online' if available else 'offline',
            'message': message,
            'model': client.model,
            'host': client.host
        })

    except Exception as e:
        logger.error(f"VLM status check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def vlm_chat(request):
    """
    VLM Chat Endpoint - Answer user questions about the dashboard.

    This endpoint implements the Visual-Time-Series Reasoning Pipeline:

    1. INPUT: Receives user question + optional snapshot ID
    2. IMAGE LOADING: Gets the latest (or specified) snapshot
    3. PROMPT CONSTRUCTION: Builds context-aware prompt
    4. VLM EXECUTION: Sends to Ollama/LLaVA
    5. RESPONSE: Returns AI-generated answer

    Request Body:
        {
            "question": "What's the correlation between gold and oil?",
            "snapshot_id": null  // Optional: use specific snapshot
        }

    Response:
        {
            "success": true,
            "answer": "Based on the charts...",
            "snapshot_used": 123
        }
    """
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        snapshot_id = data.get('snapshot_id')

        if not question:
            return JsonResponse({
                'success': False,
                'error': 'Please provide a question'
            }, status=400)

        # Get the snapshot to analyze
        if snapshot_id:
            try:
                snapshot = Snapshot.objects.get(id=snapshot_id)
            except ObjectDoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Snapshot {snapshot_id} not found'
                }, status=404)
        else:
            # Use the latest snapshot
            snapshot = Snapshot.objects.order_by('-created_at').first()
            if not snapshot:
                return JsonResponse({
                    'success': False,
                    'error': 'No snapshots available. Please save a dashboard snapshot first.'
                }, status=404)

        # Verify the image exists
        if not snapshot.image or not os.path.exists(snapshot.image.path):
            return JsonResponse({
                'success': False,
                'error': 'Snapshot image not found on disk'
            }, status=404)

        # Build context from CSV data
        context = get_csv_context()

        # Get VLM client and process the question
        from vlm_integration.vlm_client import get_vlm_client

        client = get_vlm_client()
        result = client.chat(question, snapshot.image.path, context)

        if result.get('success'):
            return JsonResponse({
                'success': True,
                'answer': result.get('response'),
                'snapshot_used': snapshot.id,
                'model': result.get('model')
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'VLM analysis failed')
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.exception("Error in VLM chat")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def vlm_analyze(request):
    """
    VLM Analysis Endpoint - Perform detailed analysis on a snapshot.

    This endpoint generates a comprehensive analysis of a dashboard snapshot,
    including trend analysis, correlation detection, and volatility assessment.

    Request Body:
        {
            "snapshot_id": 123,  // Optional: defaults to latest
            "analysis_type": "full"  // Optional: "full", "trends", "correlation"
        }

    Response:
        {
            "success": true,
            "analysis": "Detailed analysis...",
            "snapshot_id": 123
        }
    """
    try:
        data = json.loads(request.body)
        snapshot_id = data.get('snapshot_id')
        analysis_type = data.get('analysis_type', 'full')

        # Get the snapshot
        if snapshot_id:
            try:
                snapshot = Snapshot.objects.get(id=snapshot_id)
            except ObjectDoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Snapshot {snapshot_id} not found'
                }, status=404)
        else:
            snapshot = Snapshot.objects.order_by('-created_at').first()
            if not snapshot:
                return JsonResponse({
                    'success': False,
                    'error': 'No snapshots available'
                }, status=404)

        # Verify image exists
        if not snapshot.image or not os.path.exists(snapshot.image.path):
            return JsonResponse({
                'success': False,
                'error': 'Snapshot image not found'
            }, status=404)

        # Get VLM client
        from vlm_integration.vlm_client import get_vlm_client
        from vlm_integration.prompt_templates import PromptTemplates

        client = get_vlm_client()

        # Select prompt based on analysis type
        if analysis_type == 'trends':
            prompt = PromptTemplates.TREND_ANALYSIS_TEMPLATE.format(commodity="all commodities")
        elif analysis_type == 'correlation':
            prompt = PromptTemplates.CORRELATION_PROMPT_TEMPLATE.format(
                commodity1="gold", commodity2="oil"
            )
        elif analysis_type == 'volatility':
            prompt = PromptTemplates.VOLATILITY_ANALYSIS_PROMPT
        else:
            prompt = PromptTemplates.DETAILED_ANALYSIS_PROMPT

        result = client.analyze_image(
            snapshot.image.path,
            prompt,
            PromptTemplates.FINANCIAL_ANALYST_SYSTEM
        )

        if result.get('success'):
            # Optionally save the analysis to the snapshot
            if not snapshot.ai_summary:
                snapshot.ai_summary = result.get('response', '')
                snapshot.ai_analyzed = True
                snapshot.save()

            return JsonResponse({
                'success': True,
                'analysis': result.get('response'),
                'snapshot_id': snapshot.id,
                'analysis_type': analysis_type
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Analysis failed')
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.exception("Error in VLM analyze")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def vlm_regenerate_summary(request):
    """
    Regenerate AI summary for a specific snapshot.

    Useful when Ollama wasn't running during initial snapshot save.
    """
    try:
        data = json.loads(request.body)
        snapshot_id = data.get('snapshot_id')

        if not snapshot_id:
            return JsonResponse({
                'success': False,
                'error': 'snapshot_id is required'
            }, status=400)

        try:
            snapshot = Snapshot.objects.get(id=snapshot_id)
        except ObjectDoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Snapshot {snapshot_id} not found'
            }, status=404)

        # Generate new summary
        generate_ai_summary_for_snapshot(snapshot)
        snapshot.refresh_from_db()

        return JsonResponse({
            'success': True,
            'ai_summary': snapshot.ai_summary,
            'ai_analyzed': snapshot.ai_analyzed,
            'error': snapshot.ai_analysis_error or None
        })

    except Exception as e:
        logger.exception("Error regenerating summary")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def get_csv_context():
    """
    Get context data from the CSV file for VLM prompts.

    Returns a dict with latest prices, date range, and other metadata.
    """
    csv_file = os.path.join(settings.BASE_DIR, 'data', 'financial_data.csv')

    try:
        df = pd.read_csv(csv_file)
        if len(df) == 0:
            return None

        latest = df.iloc[-1]

        return {
            'latest_date': latest['date'],
            'commodities': {
                'Gold': {'price': float(latest['gold_price'])},
                'Silver': {'price': float(latest['silver_price'])},
                'Oil': {'price': float(latest['oil_price'])}
            },
            'data_points': len(df),
            'date_range': {
                'start': df['date'].iloc[0],
                'end': df['date'].iloc[-1]
            }
        }
    except Exception as e:
        logger.error(f"Error getting CSV context: {e}")
        return None
