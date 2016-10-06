from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
import django.db

import helium as He
import helium.forms as forms
import json

import logging

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
        try:
            scribble_id = int(request.POST['scribble_id'])
            score = int(request.POST['score'])
        except ValueError:
            return HttpResponse("ValueError", content_type="text/plain")
            
        logging.warn(scribble_id)
        logging.warn(score)
        logging.warn(request.POST)
        user = request.user

        scribble = He.models.ProblemScribble.objects.get(id=scribble_id)
        try:
            scribble.submitEvidence(user=user, score=score)
        except ZeroDivisionError:
            return HttpResponse("Duplicate " + str(scribble_id), content_type="text/plain")

    else:
        return HttpResponse("??", content_type="text/plain")
    return HttpResponse("OK", content_type="text/plain")

@staff_member_required
def next_scan(request):
    if request.method == 'POST':
        logging.warn(request.POST)
        try:
            problem_id = int(request.POST['problem_id'])
        except ValueError:
            return

        if problem_id == 0: 
            return

        problem = He.models.Problem.objects.get(id=problem_id)
        scribbles = He.models.ProblemScribble.objects.filter(
                verdict__problem=problem, verdict__is_done=False)
        for s in scribbles:
            # If seen before, toss out
            if s.verdict.evidence_set.filter(user=request.user).exists():
                continue
            else:
                return HttpResponse(json.dumps( [s.id, s.scan_image.url] ), 
                    content_type="application/json")
        else: # done grading!
            return HttpResponse(json.dumps( [0, ''] ), content_type="application/json")

# vim: expandtab
