from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from webapp.models import Report


@login_required
def delete_report(request, report_id):
    report = get_object_or_404(Report, id=report_id, user=request.user)
    report.delete()

    return JsonResponse({"success": True})
