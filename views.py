from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
import django.core.management
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
import threading

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

See <a href="https://www.hmmt.co/static/scoring-algorithm.pdf">https://www.hmmt.co/static/scoring-algorithm.pdf</a> for a description
of the scoring algorithm used on the individual tests.
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
    problem_id = int(request.POST['problem_id'])
    print problem_id
    if problem_id == 0: return

    problem = He.models.Problem.objects.get(id=problem_id)
    scribbles = He.models.ProblemScribble.objects.filter(
            verdict__problem=problem,
            verdict__is_done=False)
    print scribbles
    random_indices = range(0,scribbles.count())
    random.shuffle(random_indices)
    for i in random_indices:
        print i
        s = scribbles[i]
        print s
        # If seen before, toss out
        if s.verdict.evidence_set.filter(user=request.user).exists():
            continue
        else:
            return HttpResponse( json.dumps([s.id, s.scan_image.url]), \
                    content_type = 'application/json' )
    else: # done grading!
        return HttpResponse( json.dumps([0, DONE_IMAGE_URL]), \
                content_type = 'application/json' )
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
    return HttpResponse( json.dumps(output), content_type='application/json' )


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


# PRINTING OF RESULTS
def _heading(s):
    return s.upper() + "\n" + "=" * 60 + "\n"
class NameResultRow:
    rank = None # assigned by parent ExamPrinter
    def __init__(self, name, scores):
        self.name = name
        self.scores = scores
        self.total = sum(scores)
class ResultPrinter:
    def __init__(self, results):
        results.sort(key = lambda r : -r.total)
        r = 0
        for n, result in enumerate(results):
            if n == 0: r = 1
            elif results[n-1].total != result.total: r = n+1
            result.rank = r
        self.results = results
    def get_table(self, heading = None, num_show = None, num_named = None):
        output = _heading(heading) if heading is not None else ''
        for result in self.results:
            if num_show is not None and result.rank > num_show:
                break
            output += "%4d. " % result.rank
            output += "%6.3f"  % result.total if type(result.total) == float \
                    else "%6d" % result.total
            if len(result.scores) > 1: # sum of more than one thing
                output += "  |  "
                output += " ".join(["%4.2f"%x if type(x)==float else "%4d"%x \
                        for x in result.scores])
            output += "  |  "
            if num_named is None or result.rank <= num_named:
                output += result.name
            output += "\n"
        output += "\n"
        return output

def _report(num_show = None, num_named = None, teaser = False):
    output = '<!DOCTYPE html>' + "\n"
    output += '<html><head></head><body>' + "\n"
    output += '<pre style="font-family:dejavu sans mono;">' + "\n"
    output += INIT_TEXT_BANNER + "\n\n"
 
    ## Individual Results
    indiv_exams = He.models.Exam.objects.filter(is_indiv=True)
    if not teaser:
        results = [NameResultRow(name = mathlete.name_with_team,
                    scores = [He.models.get_alpha(mathlete)])
                    for mathlete in reg.MATHLETES.all()]
        output += ResultPrinter(results)\
                .get_table("Overall Individuals (Alphas)", \
                num_show = num_show, num_named = num_named)
    output += "\n"

    for exam in indiv_exams:
        results = [NameResultRow(
                name = mathlete.name_with_team,
                scores = He.models.get_exam_scores(exam, mathlete)) \
                for mathlete in reg.MATHLETES.all()]
        result_printer = ResultPrinter(results)
        output += result_printer.get_table(heading = exam.name, \
                num_show = num_show, num_named = num_named)
    output += "\n"

    ## Team Results
    team_exams = He.models.Exam.objects.filter(is_indiv=False)
    team_exam_scores = collections.defaultdict(list) # team.name -> list of scores

    for exam in team_exams:
        results = [NameResultRow(
            name = team.name,
            scores = He.models.get_exam_scores(exam, team)) \
            for team in reg.TEAMS.all()]
        result_printer = ResultPrinter(results)
        output += result_printer.get_table(heading = exam.name, \
                num_show = num_show, num_named = num_named)
        # Use for sweeps
        this_exam_weight = 400.0/max([r.total for r in results])
        for r in results:
            team_exam_scores[r.name].append(this_exam_weight * r.total)

    # Now compute individual scores
    if not teaser:
        results = []
        for team in reg.TEAMS.all():
            scores = [He.models.get_alpha(m) for m in reg.MATHLETES.filter(team = team)]
            scores.sort(reverse=True)
            results.append(NameResultRow(name = team.name, scores = scores))
        output += ResultPrinter(results).get_table(heading = "Team Individual Aggregate", \
                num_show = num_show, num_named = num_named)
        indiv_weight = 800.0/max([r.total for r in results])
        team_exam_scores[0] = {} # for indiv
        for r in results:
            team_exam_scores[r.name].append(indiv_weight * r.total)

    # Finally, sweepstakes
    if not teaser:
        output += "\n"
        results = [NameResultRow(name = team.name,
            scores = team_exam_scores[team.name])
            for team in reg.TEAMS.all()]
        output += ResultPrinter(results).get_table(heading = "Sweepstakes", \
                num_show = num_show, num_named = num_named)
   
    output += "This report was generated by Helium at " + time.strftime('%c') + "."
    output += "\n\n"
    output += FINAL_TEXT_BANNER + "\n"
    output += "</pre></body></html>"
    return HttpResponse(output, content_type="text/html")

@staff_member_required
def reports_short(request):
    return _report(num_show=10)
@staff_member_required
def reports_extended(request):
    return _report(num_named = 50)
@user_passes_test(lambda u: u.is_superuser)
def reports_full(request):
    return _report()
def teaser(request):
    """ACCESSIBLE TO NON-STAFF!"""
    return _report(num_show = 15, num_named = 0, teaser=True)

@user_passes_test(lambda u: u.is_superuser)
def run_management(request, command_name):
    def target_function():
        django.core.management.call_command(command_name)
    t = threading.Thread(target = target_function)
    t.daemon = True
    t.start()
    return HttpResponseNotFound("Command %s started" %command_name,\
            content_type="text/plain")

# vim: expandtab fdm=indent foldnestmax=1
