from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
import django.db
from registration import current as reg
import helium as He
import helium.forms as forms
import json
import logging
import itertools
import collections

@staff_member_required
def index(request):
    context = {
            'scanform' : forms.ProblemSelectForm(),
            'examform' : forms.ExamSelectForm(),
            'matchform' : forms.ExamSelectForm(),
            }
    return render(request, "helium.html", context)

def redir_exam_id(request, target):
    """To be used with ExamSelectForm. Redirects to page with correct exam ID."""
    if not request.method == "POST":
        return HttpResponseRedirect('/helium')
    form = forms.ExamSelectForm(request.POST)
    if form.is_valid():
        exam = form.cleaned_data['exam']
        logging.warn(exam)
        logging.warn(exam.id)
        return HttpResponseRedirect(target + str(exam.id))
    else:
        return HttpResponseNotFound("Invalid exam provided", content_type="text/plain")

### OLD GRADER VIEWS
@staff_member_required
def old_grader_redir(request):
    return redir_exam_id(request, target = '/helium/old-grader/')
def old_grader(request, exam_id):
    exam_id = int(exam_id)
    try:
        exam = He.models.Exam.objects.get(id=exam_id)
    except He.models.Exam.DoesNotExist:
        return HttpResponseNotFound("Exam does not exist", content_type="text/plain")
    if request.method == 'POST':
        form = forms.ExamGradingRobustForm(exam, request.user, request.POST)
        if form.is_valid():
            num_graded = form.cleaned_data['num_graded']
            whom = form.cleaned_data['whom']
            # the form cleanup actually does the processing for us,
            # so just hand the user a fresh form if no validation errors
            form = forms.ExamGradingRobustForm(exam, request.user)
            context = {
                    'exam' : exam,
                    'oldform' : form,
                    'num_graded' : num_graded,
                    'whom' : whom,
                    }
        else:
            context = {
                    'exam' : exam,
                    'oldform' : form,
                    'num_graded' : 0,
                    'whom' : None
                    }
    else:
        # This means we just got here from landing.
        # No actual grades to process yet
        context = {
                'exam' : exam,
                'oldform' : forms.ExamGradingRobustForm(exam, request.user),
                'num_graded' : 0,
                'whom' : None,
                }
    return render(request, "old-grader.html", context)

@staff_member_required
def match_exam_scans_redir(request):
    return redir_exam_id(request, target = '/helium/match-exam-scans/')
def match_exam_scans(request, exam_id):
    try:
        exam = He.models.Exam.objects.get(id=exam_id)
    except He.models.Exam.DoesNotExist:
        return HttpResponseNotFound("Exam does not exist", content_type="text/plain")

    if request.method == 'POST':
        try:
            examscribble_id = int(request.POST['examscribble_id'])
            examscribble = He.models.ExamScribble.objects.get(id=examscribble_id)
        except ValueError, He.models.ExamScribble.DoesNotExist:
            return HttpResponse("What did you DO?", content_type="text/plain")

        form = forms.ExamScribbleMatchRobustForm(examscribble, request.user, request.POST)
        if not form.is_valid(): # validation errors
            context = {
                    'matchform' : form,
                    'previous_whom' : None,
                    'scribble_url' : examscribble.scan_image.url,
                    'exam_id' : exam_id,
                    }
            return render(request, "match-exam-scans.html", context)
        else:
            previous_whom = form.cleaned_data['whom']
    else:
        previous_whom = None

    # Now we're set, so get the next scribble, or alert none left
    queryset = He.models.ExamScribble.objects.filter(mathlete=None, team=None, exam=exam)
    examscribble = queryset.first()
    if examscribble is None:
        return HttpResponse("All scanned exams have been matched", content_type="text/plain")
    form = forms.ExamScribbleMatchRobustForm(examscribble, request.user)
    context = {
            'matchform' : form,
            'previous_whom' : None,
            'scribble_url' : examscribble.scan_image.url,
            'exam_id' : exam_id,
            }
    return render(request, "match-exam-scans.html", context)


### SCAN GRADER VIEWS
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

@staff_member_required
def progress(request):
    verdicts = He.models.Verdict.objects.filter(problem__exam__is_ready=True)
    verdicts = list(verdicts)
    verdicts.sort(key = lambda v : v.problem.id)

    table = []
    columns = ['Problem', 'Done', 'Pending', 'Unread', 'Conflict', 'Missing']

    for problem, group in itertools.groupby(verdicts, key = lambda v : v.problem):
        group = list(group) # dangit, this gotcha
        tr = collections.OrderedDict()
        tr['Problem']  = str(problem)
        tr['Done']     = len([v for v in group if v.is_valid and v.is_done])
        tr['Pending']  = len([v for v in group if v.is_valid \
                and not v.is_done and v.evidence_count() > 0])
        tr['Unread']  = len([v for v in group if v.is_valid \
                and not v.is_done and v.evidence_count() == 0])
        tr['Conflict'] = len([v for v in group if not v.is_valid])
        tr['Missing']  = len(reg.MATHLETES) - len(group)
        table.append(tr)

    context = {'columns' : columns, 'table' : table}
    logging.warn(table)
    return render(request, "progress.html", context)

# vim: expandtab fdm=indent foldnestmax=1
