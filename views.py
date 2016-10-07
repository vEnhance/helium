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
    context = {
            'scanform' : forms.ProblemSelectForm(),
            'examform' : forms.ExamSelectForm()
            }
    return render(request, "helium.html", context)

@staff_member_required
def old_grader(request, exam_id=None):
    if exam_id is None:
        # Got here from landing form --- redirect to correct page
        form = forms.ExamSelectForm(request.POST)
        if form.is_valid():
            exam = form.cleaned_data['exam']
            return HttpResponseRedirect('/helium/old-grader/%d/' %exam.id)
        else:
            return HttpResponseRedirect('/helium')

    exam_id = int(exam_id)
    exam = He.models.Exam.objects.get(id=exam_id)
    if request.method == 'POST':
        form = forms.ExamGradingForm(exam, request.user, request.POST)
        if form.is_valid():
            # the form cleanup actually does the processing for us,
            # so just hand the user a fresh form if no validation errors
            form = forms.ExamGradingForm(exam, request.user)
        context = {
                'exam' : exam,
                'oldform' : form
                }
    else:
        # This means we just got here from landing.
        # No actual grades to process yet
        context = {
                'exam' : exam,
                'oldform' : forms.ExamGradingForm(exam, request.user)
                }

    return render(request, "old-grader.html", context)


@staff_member_required
def grade_scans(request):
    if request.method == 'GET':
        form = forms.ProblemSelectForm(request.GET)
        if form.is_valid():
            problem = form.cleaned_data['problem']
            answer = problem.answer
            return render(request, "grade-scans.html",
                    {'problem':problem})
    else:
        return render(request, "grade-scans.html", {'problem':''})

@staff_member_required
def submit_scan(request):
    # Takes in (from AJAX POST) a scribble id and score
    # and enters it as evidence into the database
    if request.method == 'POST':
        try:
            scribble_id = int(request.POST['scribble_id'])
            score = int(request.POST['score'])
        except ValueError:
            return HttpResponse("ValueError", content_type="text/plain")
        user = request.user
        scribble = He.models.ProblemScribble.objects.get(id=scribble_id)
        scribble.submitEvidence(user=user, score=score, god_mode=False)
    else:
        return HttpResponse("??", content_type="text/plain")
    return HttpResponse("OK", content_type="text/plain")

@staff_member_required
def next_scan(request):
    if request.method == 'POST':
        try:
            problem_id = int(request.POST['problem_id'])
        except ValueError:
            return
        if problem_id == 0: 
            return

        problem = He.models.Problem.objects.get(id=problem_id)
        scribbles = He.models.ProblemScribble.objects.filter(
                verdict__problem=problem,
                verdict__is_done=False)
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
