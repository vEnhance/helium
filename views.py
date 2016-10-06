from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
import django.db

import helium as He
import helium.forms as forms
import json

import logging
logger = logging.getLogger(__name__)

# Create your views here.


@staff_member_required
def index(request):
    scanform = forms.ProblemScanForm()
    return render(request, "helium-landing.html",
            {'scanform' : scanform})

@staff_member_required
def grade_scans(request):
    if request.method == 'GET':
        form = forms.ProblemScanForm(request.GET)
        if form.is_valid():
            problem = form.cleaned_data['problem']
            answer = problem.answer
            return render(request, "grade-scans.html",
                    {'problem':problem})
    else:
        return render(request, "grade-scans.html", {'problem':''})

@staff_member_required
def submit_scan(request):
    if request.method == 'POST':
        print request.POST
        scribble_id = int(request.POST['scribble_id'])
        score = int(request.POST['score'])
        user = request.user

        scribble = He.models.ProblemScribble.objects.get(id=scribble_id)
        try:
            scribble.submitEvidence(user=user, score=score)
        except django.db.IntegrityError:
            return HttpResponse("Duplicate", content_type="text/plain")

    else:
        raise HttpResponse("??", content_type="text/plain")
    return HttpResponse("OK", content_type="text/plain")

@staff_member_required
def next_scan(request):
    if request.method == 'POST':
        problem_id = int(request.POST['problem_id'])
        problem = He.models.Problem.objects.get(id=problem_id)
        scribbles = He.models.ProblemScribble.objects.filter(
                verdict__problem=problem, verdict__is_done=False)
        if len(scribbles) > 0:
            return HttpResponse(str(scribbles), content_type="text/plain")

# vim: expandtab
