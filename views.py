from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.views.decorators.http import require_POST
import django.db
from registration import current as reg
import helium as He
import helium.forms as forms
import json
import logging
import itertools
import collections
import random

DONE_IMAGE_URL = static('img/done.jpg')

def redir_obj_id(request, target, key, form_type):
    """To be used with a select form. Redirects to page with correct ID."""
    if not request.method == "POST":
        return HttpResponseRedirect('/helium')
    form = form_type(request.POST)
    if form.is_valid():
        obj = form.cleaned_data[key]
        logging.warn(obj)
        logging.warn(obj.id)
        return HttpResponseRedirect(target + str(obj.id))
    else:
        return HttpResponseNotFound("Invalid object ID provided", content_type="text/plain")

@staff_member_required
def index(request):
    context = {
            'scanform' : forms.ProblemSelectForm(),
            'examform' : forms.ExamSelectForm(),
            'matchform' : forms.ExamSelectForm(),
            }
    return render(request, "helium.html", context)

@staff_member_required
def old_grader_redir(request):
    return redir_obj_id(request,
            target = '/helium/old-grader/',
            key = 'exam',
            form_type = forms.ExamSelectForm)
@staff_member_required
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
    return redir_obj_id(request,
            target = '/helium/match-exam-scans/',
            key = 'exam',
            form_type = forms.ExamSelectForm)
@staff_member_required
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
                    'exam' : exam,
                    }
            return render(request, "match-exam-scans.html", context)
        else:
            previous_whom = form.cleaned_data['whom']
    else:
        previous_whom = None

    # Now we're set, so get the next scribble, or alert none left
    queryset = He.models.ExamScribble.objects.filter(mathlete=None, team=None, exam=exam)

    if len(queryset) == 0:
        context = {
                'matchform' : None,
                'previous_whom' : previous_whom,
                'scribble_url' : DONE_IMAGE_URL,
                'exam' : exam,
                }
    else:
        examscribble = queryset[random.randrange(queryset.count())]
        form = forms.ExamScribbleMatchRobustForm(examscribble, request.user)
        context = {
                'matchform' : form,
                'previous_whom' : previous_whom,
                'scribble_url' : examscribble.scan_image.url,
                'exam' : exam,
                }
    return render(request, "match-exam-scans.html", context)

@staff_member_required
def grade_scans_redir(request):
    return redir_obj_id(request,
            target = '/helium/grade-scans/',
            key = 'problem',
            form_type = forms.ProblemSelectForm)
@staff_member_required
def grade_scans(request, problem_id):
    problem = He.models.Problem.objects.get(id=problem_id)
    return render(request, "grade-scans.html",
            {'problem' : problem, 'exam': problem.exam})

@staff_member_required
@require_POST
def ajax_submit_scan(request):
    """POST arguments: scribble_id, score. RETURN: nothing useful"""
    try:
        scribble_id = int(request.POST['scribble_id'])
        score = int(request.POST['score'])
    except ValueError: return
    user = request.user
    scribble = He.models.ProblemScribble.objects.get(id=scribble_id)
    scribble.submitEvidence(user=user, score=score, god_mode=False)
    return HttpResponse("OK", content_type="text/plain")
@staff_member_required
@require_POST
def ajax_next_scan(request):
    """POST arguments: problem_id. RETURN: (scribble id, scribble url)"""
    try:
        problem_id = int(request.POST['problem_id'])
    except ValueError:
        return
    if problem_id == 0: return

    problem = He.models.Problem.objects.get(id=problem_id)
    scribbles = He.models.ProblemScribble.objects.filter(
            verdict__problem=problem,
            verdict__is_done=False)
    random_indices = range(0,scribbles.count())
    random.shuffle(random_indices)
    for i in random_indices:
        s = scribbles[i]
        # If seen before, toss out
        if s.verdict.evidence_set.filter(user=request.user).exists():
            continue
        else:
            return HttpResponse(json.dumps( [s.id, s.scan_image.url] ), 
                content_type="application/json")
    else: # done grading!
        return HttpResponse(json.dumps( [0, DONE_IMAGE_URL] ),
                content_type="application/json")
@staff_member_required
@require_POST
def ajax_prev_evidence(request):
    """POST arguments: problem_id, and either id_mathlete / id_team.
    RETURN: a tuple of previous responses (starting with None)."""
    try:
        exam_id = int(request.POST['problem_id'])
    except ValueError:
        return
    



@staff_member_required
def progress_problems(request):
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

    context = {'columns' : columns, 'table' : table, 'pagetitle' : 'Scans Progress'}
    logging.warn(table)
    return render(request, "gentable.html", context)
@staff_member_required
def progress_scans(request):
    examscribbles = He.models.ExamScribble.objects.filter(exam__is_ready=True)
    examscribbles = list(examscribbles)
    examscribbles.sort(key = lambda es : es.exam.id)

    table = []
    columns = ['Exam', 'Done', 'Left']

    for exam, group in itertools.groupby(examscribbles, key = lambda es : es.exam):
        group = list(group) # dangit, this gotcha
        tr = collections.OrderedDict()
        tr['Exam'] = str(exam)
        tr['Done'] = len([es for es in group if es.whom is not None])
        tr['Left'] = len(group) - tr['Done']
        table.append(tr)

    context = {'columns' : columns, 'table' : table, 'pagetitle' : 'Scans Progress'}
    logging.warn(table)
    return render(request, "gentable.html", context)


# vim: expandtab fdm=indent foldnestmax=1
