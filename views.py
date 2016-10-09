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
import time

DONE_IMAGE_URL = static('img/done.jpg')

INIT_TEXT_BANNER = """
 .----------------.  .----------------.  .----------------.  .----------------. 
| .--------------. || .--------------. || .--------------. || .--------------. |
| |  ____  ____  | || | ____    ____ | || | ____    ____ | || |  _________   | |
| | |_   ||   _| | || ||_   \  /   _|| || ||_   \  /   _|| || | |  _   _  |  | |
| |   | |__| |   | || |  |   \/   |  | || |  |   \/   |  | || | |_/ | | \_|  | |
| |   |  __  |   | || |  | |\  /| |  | || |  | |\  /| |  | || |     | |      | |
| |  _| |  | |_  | || | _| |_\/_| |_ | || | _| |_\/_| |_ | || |    _| |_     | |
| | |____||____| | || ||_____||_____|| || ||_____||_____|| || |   |_____|    | |
| |              | || |              | || |              | || |              | |
| '--------------' || '--------------' || '--------------' || '--------------' |
 '----------------'  '----------------'  '----------------'  '----------------' 
 """.strip()

FINAL_TEXT_BANNER = """ 
 ('-. .-.   ('-.                               _   .-')    
( OO )  / _(  OO)                             ( '.( OO )_  
,--. ,--.(,------.,--.      ,-.-') ,--. ,--.   ,--.   ,--.)
|  | |  | |  .---'|  |.-')  |  |OO)|  | |  |   |   `.'   | 
|   .|  | |  |    |  | OO ) |  |  \|  | | .-') |         | 
|       |(|  '--. |  |`-' | |  |(_/|  |_|( OO )|  |'.'|  | 
|  .-.  | |  .--'(|  '---.',|  |_.'|  | | `-' /|  |   |  | 
|  | |  | |  `---.|      |(_|  |  ('  '-'(_.-' |  |   |  | 
`--' `--' `------'`------'  `--'    `-----'    `--'   `--'""".strip()


def _redir_obj_id(request, target, key, form_type):
    """To be used with a select form. Redirects to page with correct ID."""
    if not request.method == "POST":
        return HttpResponseRedirect('/helium')
    form = form_type(request.POST)
    if form.is_valid():
        obj = form.cleaned_data[key]
        return HttpResponseRedirect(target + str(obj.id))
    else:
        return HttpResponseNotFound("Invalid object ID provided", content_type="text/plain")
def _json(obj):
    return HttpResponse(json.dumps(obj), content_type='application/json')

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
    return _redir_obj_id(request,
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
    return _redir_obj_id(request,
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
    return _redir_obj_id(request,
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
            return _json( [s.id, s.scan_image.url] ),
    else: # done grading!
        return _json( [0, DONE_IMAGE_URL ] )
@staff_member_required
@require_POST
def ajax_prev_evidence(request):
    """POST arguments: problem_id, and either id_mathlete / id_team.
    RETURN: a list of pairs (num, answer) where answer may be None"""
    try:
        exam_id     = int(request.POST['exam_id'])
        exam = He.models.Exam.objects.get(id = exam_id)
        if exam.is_indiv:
            mathlete_id = int(request.POST['mathlete_id'])
        else:
            team_id     = int(request.POST['team_id'])
    except ValueError:
        return
    output = []
    for problem in exam.problem_set.all().order_by('problem_number'):
        n = problem.problem_number
        try:
            if exam.is_indiv:
                e = He.models.Evidence.objects.get(
                        user = request.user,
                        verdict__problem = problem,
                        verdict__mathlete_id = mathlete_id)
            else:
                e = He.models.Evidence.objects.get(
                        user = request.user,
                        verdict__problem = problem,
                        verdict__team_id = team_id)
        except He.models.Evidence.DoesNotExist:
            output.append( (n, None) )
        else:
            output.append( (n, e.score) )
    return _json( output )


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
    return render(request, "gentable.html", context)


def _heading(s):
    return s.upper() + "\n" + "=" * 80 + "\n"

class NameResultRow:
    rank = None # assigned by parent ExamPrinter
    def __init__(self, name, scores = None, total = None):
        self.name = name
        if scores is not None:
            self.scores = scores
            self.total = sum(scores)
        else:
            self.total = total
class ResultPrinter:
    def __init__(self, results):
        results.sort(key = lambda r : -r.total)
        r = 0
        for n, result in enumerate(results):
            if n == 0: r = 1
            elif results[n-1].total != result.total: r = n+1
            result.rank = r
        self.results = results
    def get_table(self, exam = None):
        output = _heading(unicode(exam)) if exam is not None else ""
        for result in self.results:
            output += "%4d. " % result.rank
            output += "%6.3f"  % result.total if type(result.total) == float \
                    else "%6d" % result.total
            if exam is not None:
                output += "  |  "
                output += " ".join(["%4.1f"%x if type(x)==float else "%4d"%x \
                        for x in result.scores])
            output += "  |  "
            output += result.name
            output += "\n"
        output += "\n"
        return output

@staff_member_required
def reports_individual(request):
    indiv_exams = He.models.Exam.objects.filter(is_indiv=True, is_ready=True)
    output = '<pre style="font-family:dejavu sans mono;">' + "\n"
    output += INIT_TEXT_BANNER + "\n\n"
 
    output += _heading("Top Individuals")
    results = [NameResultRow(name = mathlete.name_with_team,
                total = He.models.MathleteAlpha.objects\
                        .get(mathlete=mathlete).cached_alpha)
                for mathlete in reg.MATHLETES.all()]
    output += ResultPrinter(results).get_table(exam = None)

    for exam in indiv_exams:
        results = [NameResultRow(
                name = mathlete.name_with_team,
                scores = He.models.get_exam_scores(exam, mathlete)) \
                for mathlete in reg.MATHLETES.all()]
        result_printer = ResultPrinter(results)
        output += result_printer.get_table(exam)
        output += "\n"*2
   
    output += "\n\n"
    output += "This report was generated by Helium at " + time.strftime('%c')
    output += "\n\n"
    output += FINAL_TEXT_BANNER + "\n"
    output += "</pre>"
    return HttpResponse(output, content_type="text/html")

# vim: expandtab fdm=indent foldnestmax=1
