"""
HELIUM
Evan Chen, 2016

views.py

This is the massive views.py.

CONVENTION: Name of view function is always the URL
with all dashes and slashes replaced by underscores

This file is divided into roughly a few parts:

## Grading views: for example
* The classical grader (old_grader), grade by name and test
* The exam scan matching interface (match_exam_scans)
* The scan grader (grade_scans), grading problem scans

## AJAX hooks
These are ajax_*. Used by scan grading.

## Progress reports
progress_*, shows how much progress we've made grading.

## Results
reports_*, this shows the results of the tournament.
This includes also teaser and spreadsheet.

## Misc
run_management, for management commands
index, the main landing page.
"""


from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
import django.core.management
import django.db
import json
import logging
import itertools
import collections
import random
import time
import threading

import helium as He
import helium.forms as forms
import presentation

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
`--' `--' `------'`------'  `--'    `-----'    `--'   `--' 
""".strip()


def _redir_obj_id(request, target, key, form_type):
	"""To be used with a select form. Redirects to page with correct ID.
	For example, if you use an ExamSelectForm and POST to /helium/match-exam-scans/
	this will send a redirec to /helium/match-exam-scans/<exam.id>"""
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
	"""This prints the main lainding page helium.html"""
	context = {
			'scanform' : forms.ProblemScanSelectForm(),
			'examform' : forms.ExamSelectForm(),
			'matchform' : forms.ExamScanSelectForm(),
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
			entity = form.cleaned_data['entity']
			# the form cleanup actually does the processing for us,
			# so just hand the user a fresh form if no validation errors
			form = forms.ExamGradingRobustForm(exam, request.user)
			context = {
					'exam' : exam,
					'oldform' : form,
					'num_graded' : num_graded,
					'entity' : entity,
					}
		else:
			context = {
					'exam' : exam,
					'oldform' : form,
					'num_graded' : 0,
					'entity' : None
					}
	else:
		# This means we just got here from landing.
		# No actual grades to process yet
		context = {
				'exam' : exam,
				'oldform' : forms.ExamGradingRobustForm(exam, request.user),
				'num_graded' : 0,
				'entity' : None,
				}
	return render(request, "old-grader.html", context)


@staff_member_required
def match_exam_scans_redir(request):
	return _redir_obj_id(request,
			target = '/helium/match-exam-scans/',
			key = 'exam',
			form_type = forms.ExamScanSelectForm)
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
					'previous_entity' : None,
					'scribble' : examscribble,
					'scribble_url' : examscribble.scan_image.url,
					'exam' : exam,
					}
			return render(request, "match-exam-scans.html", context)
		else:
			previous_entity = form.cleaned_data['entity']
	else:
		previous_entity = None

	# Now we're set, so get the next scribble, or alert none left
	queryset = He.models.ExamScribble.objects.filter(entity=None, exam=exam)

	if len(queryset) == 0:
		context = {
				'matchform' : None,
				'previous_entity' : previous_entity,
				'scribble' : None,
				'scribble_url' : DONE_IMAGE_URL,
				'exam' : exam,
				}
	else:
		examscribble = queryset[random.randrange(queryset.count())]
		form = forms.ExamScribbleMatchRobustForm(examscribble, request.user)
		context = {
				'matchform' : form,
				'previous_entity' : previous_entity,
				'scribble' : examscribble,
				'scribble_url' : examscribble.scan_image.url,
				'exam' : exam,
				}
	return render(request, "match-exam-scans.html", context)


@staff_member_required
def grade_scans_redir(request):
	return _redir_obj_id(request,
			target = '/helium/grade-scans/',
			key = 'problem',
			form_type = forms.ProblemScanSelectForm)
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
	RETURN: a list of pairs (problem_number, answer) where answer may be None"""
	try:
		exam_id = int(request.POST['exam_id'])
		exam = He.models.Exam.objects.get(id = exam_id)
		entity_id = int(request.POST['entity_id'])
	except ValueError:
		return
	output = []
	for problem in exam.problem_set.all().order_by('problem_number'):
		n = problem.problem_number
		try:
			e = He.models.Evidence.objects.get(
					user = request.user,
					verdict__problem = problem,
					verdict__entity__id = entity_id)
		except He.models.Evidence.DoesNotExist:
			output.append( (n, None) )
		else:
			output.append( (n, e.score) )
	return HttpResponse( json.dumps(output), content_type='application/json' )


@staff_member_required
def progress_problems(request):
	"""Generates a table of how progress grading the problem is going."""
	verdicts = He.models.Verdict.objects.filter(problem__exam__is_ready=True)
	verdicts = list(verdicts)
	verdicts.sort(key = lambda v : v.problem.id)

	table = []
	columns = ['Problem', 'Done', 'Pending', 'Unread', 'Conflict', 'Missing']

	num_mathletes = He.models.Entity.mathletes.count()
	for problem, group in itertools.groupby(verdicts, key = lambda v : v.problem):
		group = list(group) # dangit, this gotcha
		tr = collections.OrderedDict()
		tr['Problem']  = str(problem)
		tr['Done']     = len([v for v in group if v.is_valid and v.is_done])
		tr['Pending']  = len([v for v in group if v.is_valid \
				and not v.is_done and v.evidence_count() > 0])
		tr['Unread']   = len([v for v in group if v.is_valid \
				and not v.is_done and v.evidence_count() == 0])
		tr['Conflict'] = len([v for v in group if not v.is_valid])
		tr['Missing']  = num_mathletes - len(group)
		table.append(tr)

	context = {'columns' : columns, 'table' : table, 'pagetitle' : 'Grading Progress'}
	return render(request, "gentable.html", context)

@staff_member_required
def progress_scans(request):
	"""Generates a table showing how quickly the scans are being matched for a problem."""
	examscribbles = He.models.ExamScribble.objects\
			.filter(exam__is_ready=True, exam__is_scanned=True)
	examscribbles = list(examscribbles)
	examscribbles.sort(key = lambda es : es.exam.id)

	table = []
	columns = ['Exam', 'Done', 'Left']

	for exam, group in itertools.groupby(examscribbles, key = lambda es : es.exam):
		group = list(group) # dangit, this gotcha
		tr = collections.OrderedDict()
		tr['Exam'] = str(exam)
		tr['Done'] = len([es for es in group if es.entity is not None])
		tr['Left'] = len(group) - tr['Done']
		table.append(tr)

	context = {'columns' : columns, 'table' : table, 'pagetitle' : 'Scans Progress'}
	return render(request, "gentable.html", context)

def _report(num_show = None, num_named = None,
		show_indiv_alphas = True, show_team_sum_alphas = True, show_hmmt_sweepstakes = True):
	"""Explanation of potions:
	num_show: Display only the top N entities
	num_named: Suppress the names of entities after rank N
	The other booleans are self explanatory."""

	output = '<!DOCTYPE html>' + "\n"
	output += '<html><head></head><body>' + "\n"
	output += '<pre style="font-family:dejavu sans mono;">' + "\n"
	output += INIT_TEXT_BANNER + "\n\n"

	# Do this query once, we'll need it repeatedly
	mathletes = list(He.models.Entity.mathletes.all())
	teams = list(He.models.Entity.teams.all())
 
	## Individual Results
	if show_indiv_alphas:
		output += presentation.RP_alphas(mathletes).get_table("Overall Individuals (Alphas)", \
				num_show = num_show, num_named = num_named)
	output += "\n"

	indiv_exams = He.models.Exam.objects.filter(is_indiv=True)
	for exam in indiv_exams:
		output += presentation.RP_exam(exam, mathletes).get_table(heading = unicode(exam), \
				num_show = num_show, num_named = num_named)
	output += "\n"

	## Team Results
	team_exams = He.models.Exam.objects.filter(is_indiv=False)
	if show_hmmt_sweepstakes:
		team_exam_scores = collections.defaultdict(list) # unicode(team) -> list of scores

	for exam in team_exams:
		rp = presentation.RP_exam(exam, teams)
		output += rp.get_table(heading = unicode(exam), \
				num_show = num_show, num_named = num_named,
				float_string = "%2.0f", int_string = "%2d")
		# Use for sweeps
		if show_hmmt_sweepstakes:
			if len(rp.results) > 0 and any([r.total for r in rp.results]):
				this_exam_weight = 400.0/max([r.total for r in rp.results])
			else:
				this_exam_weight = 0 # nothing yet
			for r in rp.results:
				team_exam_scores[r.row_name].append(this_exam_weight * r.total)

	# Now compute sum of individual scores
	if show_team_sum_alphas:
		rp = presentation.RP_alpha_sums(mathletes, teams)
		output += rp.get_table(heading = "Team Individual Aggregate", \
				num_show = num_show, num_named = num_named)
		if show_hmmt_sweepstakes:
			if len(rp.results) > 0 and any([r.total for r in rp.results]):
				indiv_weight = 800.0/max([r.total for r in rp.results])
			else:
				indiv_weight = 0 # nothing yet
			for r in rp.results:
				team_exam_scores[r.row_name].append(indiv_weight * r.total)

	# Finally, sweepstakes
	if show_hmmt_sweepstakes:
		output += "\n"
		results = [presentation.NameResultRow(row_name = unicode(team),
			scores = team_exam_scores[unicode(team)])
			for team in teams]
		output += presentation.ResultPrinter(results).get_table(heading = "Sweepstakes", \
				num_show = num_show, num_named = num_named,
				float_string = "%6.2f", int_string = "%6d")
   
	output += "This report was generated by Helium at " + time.strftime('%c') + "."
	output += "\n\n"
	output += FINAL_TEXT_BANNER + "\n"
	output += "</pre></body></html>"
	return HttpResponse(output, content_type="text/html")

@staff_member_required
def reports_short(request):
	return _report(num_show = 10)
@staff_member_required
def reports_extended(request):
	return _report(num_named = 50)
@user_passes_test(lambda u: u.is_superuser)
def reports_full(request):
	return _report()
def teaser(request):
	"""ACCESSIBLE TO NON-STAFF!"""
	return _report(num_show = 15, num_named = 0,
			show_indiv_alphas = False,
			show_team_sum_alphas = False,
			show_hmmt_sweepstakes = False)

@user_passes_test(lambda u: u.is_superuser)
def spreadsheet(request):
	"""Get the entire score spreadsheet."""

	mathletes = list(He.models.Entity.mathletes.all())
	teams = list(He.models.Entity.teams.all())

	sheets = {} # sheet name -> rows

	# Individual alphas, but only if someone has nonzero alpha
	if He.models.EntityAlpha.objects.filter(cached_alpha__gt=0).exists():
		sheets['Alpha'] = presentation.RP_alphas(mathletes).get_rows()

	indiv_exams = He.models.Exam.objects.filter(is_indiv=True)
	for exam in indiv_exams:
		sheets[unicode(exam)] = presentation.RP_exam(exam, mathletes).get_rows()
	team_exams = He.models.Exam.objects.filter(is_indiv=False)
	for exam in team_exams:
		sheets[unicode(exam)] = presentation.RP_exam(exam, teams).get_rows()

	spreadsheet = presentation.get_odf_spreadsheet(sheets)
	response = HttpResponse(spreadsheet,\
			content_type="application/vnd.oasis.opendocument.spreadsheet")
	response['Content-Disposition'] = 'attachment; filename=scores-%s.ods' \
			%time.strftime("%Y%m%d-%H%M%S")
	return response

@user_passes_test(lambda u: u.is_superuser)
def run_management(request, command_name):
	"""Starts a thread which runs a specified management command"""
	def target_function():
		django.core.management.call_command(command_name)
	t = threading.Thread(target = target_function)
	t.daemon = True
	t.start()
	return HttpResponse("Command %s started" %command_name,\
			content_type="text/plain")

# vim: fdm=indent foldnestmax=1
