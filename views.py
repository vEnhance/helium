"""
HELIUM
(c) 2016 Evan Chen
See LICENSE.txt for details.

views.py

This is the massive views.py.

CONVENTION: Name of view function is always the URL
with all dashes and slashes replaced by underscores

This file is divided into roughly a few parts:

## Grading views: for example
* The classical grader (old_grader_*), grade by name and test/problem
* The interface matching papers to students (match_papers)
* Interfaces view_* for viewing previous evidences and maybe fixing them
* The scan grader (grade_scans), grading problem scans

## Verdict views
view_*
The interfaces view_verdict and find_verdicts, etc.
These are used so that e.g. you can look at your own grading conflicts.
Also view_paper for viewing an entire examscribble

## AJAX hooks
These are ajax_*. Used by scan grading.

## Upload scans
upload_scans, uploading scans for exams

## Progress reports
progress_*, shows how much progress we've made grading.

## Score reports
reports_*, this shows the results of the tournament.
This includes also teaser and spreadsheet.

## Misc
estimation_calc, a widget to compute partial marks for Guts round
run_management, for management commands
index, the main landing page.
"""


from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Count
import django.core.management
import django.db
import json
import logging
import collections
import random
import time

# The following imports are Helium specific
import helium as He
import helium.forms as forms
import presentation
import scanimage
import threader

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

HELIUM (c) 2016 Evan Chen
""".strip()


def _redir_obj_id(request, key, form_type):
	"""To be used with a select form. Redirects to page with correct ID.
	For example, if you use an ExamSelectForm and POST to /helium/match-papers/
	this will send a redirect to /helium/match-papers/<exam.id>.
	
	:request: the request
	:key: the key from the form
	:form_type: the class for the form"""
	if not request.method == "POST":
		return HttpResponseRedirect('/helium')
	form = form_type(request.POST)
	if form.is_valid():
		obj = form.cleaned_data[key]
		return HttpResponseRedirect(request.path.replace('redir', str(obj.id)))
	else:
		return HttpResponseNotFound("Invalid object ID provided", content_type="text/plain")

@staff_member_required
def index(request):
	"""This prints the main landing page helium.html"""
	context = {
			'problemscanform' : forms.ProblemScanSelectForm(),
			'examscanform' : forms.ExamScanSelectForm(),
			'problemform' : forms.ProblemNoScanSelectForm(),
			'examform' : forms.ExamNoScanSelectForm(),
			}
	return render(request, "helium.html", context)

## VIEWS FOR CLASSICAL GRADER
def _old_grader(request, exam, problems):
	if request.method == 'POST':
		form = forms.ExamGradingRobustForm(request.POST,
				exam = exam, problems = problems, user = request.user)
		if form.is_valid():
			num_graded = form.cleaned_data['num_graded']
			entity = form.cleaned_data['entity']
			# the form cleanup actually does the processing for us,
			# so just hand the user a fresh form if no validation errors
			form = forms.ExamGradingRobustForm(
					exam = exam, problems = problems, user = request.user)
			context = {
					'exam' : exam,
					'form' : form,
					}
			messages.success(request, "Successfully graded %d problems for %s" \
					%(num_graded, entity))
		else:
			context = {
					'exam' : exam,
					'form' : form,
					}
	else:
		# This means we just got here from landing.
		# No actual grades to process yet
		context = {
				'exam' : exam,
				'form' : forms.ExamGradingRobustForm(
					exam = exam, problems = problems, user = request.user),
				}
	return render(request, "old-grader.html", context)
@staff_member_required
def old_grader_exam_redir(request):
	return _redir_obj_id(request,
			key = 'exam',
			form_type = forms.ExamNoScanSelectForm)
@staff_member_required
def old_grader_exam(request, exam_id):
	exam = He.models.Exam.objects.get(id=int(exam_id))
	problems = exam.problems.all()
	return _old_grader(request, exam, problems)
	
@staff_member_required
def old_grader_problem_redir(request):
	return _redir_obj_id(request,
			key = 'problem',
			form_type = forms.ProblemNoScanSelectForm)
@staff_member_required
def old_grader_problem(request, problem_id):
	problem = He.models.Problem.objects.get(id=int(problem_id))
	exam = problem.exam
	problems = [problem]
	return _old_grader(request, exam, problems)

## VIEWS FOR SLOW SCAN MATCH
@staff_member_required
def match_papers_redir(request):
	return _redir_obj_id(request,
			key = 'exam',
			form_type = forms.ExamScanSelectForm)
@staff_member_required
def match_papers(request, exam_id):
	try:
		exam = He.models.Exam.objects.get(id=exam_id)
	except He.models.Exam.DoesNotExist:
		return HttpResponseNotFound("Exam does not exist", content_type="text/plain")

	if request.method == 'POST':
		try:
			examscribble_id = int(request.POST['examscribble_id'])
			examscribble = He.models.ExamScribble.objects.get(id=examscribble_id)
		except (ValueError, He.models.ExamScribble.DoesNotExist):
			return HttpResponse("What did you DO?", content_type="text/plain")

		form = forms.ExamScribbleMatchRobustForm(
				request.POST, examscribble = examscribble, user = request.user)
		if form.is_valid():
			prev_entity = form.cleaned_data['entity']
			if form.cleaned_data['attention']:
				messages.success(request, "Marked exam scribble for admin action "
				"(reason given: %s)" % form.cleaned_data['attention'])
			else:
				messages.success(request, "Matched exam for %s" %prev_entity)
		else: # validation errors
			context = {
					'form' : form,
					'scribble' : examscribble,
					'exam' : exam,
					}
			return render(request, "match-papers.html", context)

	# Now we're set, so get the next scribble, or alert none left
	queryset = He.models.ExamScribble.objects.filter\
			(entity=None, exam=exam, needs_attention=u'')

	if len(queryset) == 0:
		context = {
				'form' : None,
				'scribble' : None,
				'exam' : exam,
				}
	else:
		examscribble = queryset[random.randrange(queryset.count())]
		form = forms.ExamScribbleMatchRobustForm(
				examscribble = examscribble, user = request.user)
		context = {
				'form' : form,
				'scribble' : examscribble,
				'exam' : exam,
				}
	return render(request, "match-papers.html", context)

## VIEWS FOR FAST SCAN MATCH
@staff_member_required
def fast_match_redir(request):
	return _redir_obj_id(request,
			key = 'exam',
			form_type = forms.ExamScanSelectForm)
@staff_member_required
def fast_match(request, exam_id):
	try:
		exam = He.models.Exam.objects.get(id=exam_id)
	except He.models.Exam.DoesNotExist:
		return HttpResponseNotFound("Exam does not exist", content_type="text/plain")
	return render(request, "fast-match.html", context)

## VIEWS FOR SCAN GRADER
@staff_member_required
def grade_scans_redir(request):
	return _redir_obj_id(request,
			key = 'problem',
			form_type = forms.ProblemScanSelectForm)
@staff_member_required
def grade_scans(request, problem_id):
	problem = He.models.Problem.objects.get(id=int(problem_id))
	return render(request, "grade-scans.html",
			{'problem' : problem, 'exam': problem.exam})

## VIEWS FOR VERDICTS AND SCANS
def _get_vtable(request, verdicts):
	table = []
	columns = ['Entity', 'Problem', 'Score', 'Num Grades', 'View']
	for verdict in verdicts:
		tr = collections.OrderedDict()
		tr['Entity'] = verdict.entity
		tr['Problem'] = verdict.problem
		tr['Score'] = verdict.score if verdict.score is not None else "?"
		tr['Num Grades'] = verdict.evidence_set.count()
		tr['View'] = "<a href=\"/helium/view-verdict/%d/\">Open</a>" \
				% verdict.id
		table.append(tr)
	return columns, table
@staff_member_required
def view_verdict(request, verdict_id):
	verdict = He.models.Verdict.objects.get(id = int(verdict_id))
	form_args = {
			'entity' : verdict.entity,
			'exam' : verdict.problem.exam,
			'problems' : [verdict.problem],
			'user' : request.user,
			'show_god' : request.user.is_superuser,
			}

	if request.method == 'POST':
		form = forms.ExamGradingRobustForm(request.POST, **form_args)
		if form.is_valid(): # and we're done!
			entity = form.cleaned_data['entity']
			messages.success(request, "Successfully submitted evidence for %s" % entity)
	else:
		form = forms.ExamGradingRobustForm(**form_args)

	verdict.refresh_from_db()
	table = []
	columns = ['Score', 'User', 'God Mode']
	for evidence in verdict.evidence_set.all():
		tr = collections.OrderedDict()
		tr['Score'] = evidence.score
		tr['User'] = evidence.user
		if request.user == evidence.user:
			tr['User'] = '<b>' + str(tr['User']) + '</b>'
		tr['God Mode'] = str(evidence.god_mode)
		table.append(tr)
	context = {'columns' : columns, 'table' : table, 'form' : form, 'verdict' : verdict}
	return render(request, "view-verdict.html", context)
@staff_member_required
def find_paper(request):
	if request.method == "POST":
		form = forms.EntityExamSelectForm(request.POST)
		if form.is_valid():
			entity = form.cleaned_data['entity']
			exam = form.cleaned_data['exam']
			return HttpResponseRedirect("/helium/view-paper/%d/%d/" \
					%(entity.id,exam.id))
	else:
		form = forms.EntityExamSelectForm()
	context = { 'eesform' : form, 'pdfform' : forms.PDFSelectForm() }
	if request.user.is_superuser:
		context['show_attention'] = True
		context['columns'] = ['Reason', 'Exam', 'Entity', 'Open']
		table = []
		# List scribbles needing attention
		for es in He.models.ExamScribble.objects.exclude(needs_attention=u''):
			tr = collections.OrderedDict()
			tr['Reason'] = es.needs_attention # reason in queue
			tr['Exam'] = es.exam
			tr['Entity'] = es.entity
			tr['Open'] = '<a href="/helium/view-paper/scan/%d">Open</a>' %es.id
			table.append(tr)
		context['table'] = table
	else:
		context['show_attention'] = False
		
	return render(request, "find-paper.html", context)
@staff_member_required
def view_paper(request, *args):
	if len(args) == 1: # view-paper/scan/examscribble.id/
		es = He.models.ExamScribble.objects.get(id = int(args[0]))
		entity = es.entity
		exam = es.exam
	elif len(args) == 2: # view-paper/entity.id/exam.id/
		entity = He.models.Entity.objects.get(id = int(args[0]))
		exam = He.models.Exam.objects.get(id = int(args[1]))
		try:
			es = He.models.ExamScribble.objects.get(entity=entity, exam=exam)
		except He.models.ExamScribble.DoesNotExist:
			es = None
	context = {}
	if es:
		context['title'] = unicode(es)
		context['examscribble'] = es
		verdicts = He.models.Verdict.objects\
				.filter(problemscribble__examscribble = es)
	else:
		context['title'] = "%s for %s" %(entity, exam)
		verdicts = He.models.Verdict.objects\
				.filter(problem__exam = exam, entity = entity)
	context['columns'], context['table'] =  _get_vtable(request, verdicts)
	context['exam'] = exam
	context['entity'] = entity

	if es is not None:
		if request.method == "POST":
			form = forms.NeedsAttentionForm(request.POST, instance=es)
			if form.is_valid():
				messages.success(request, "Changed the status of this PDF")
				form.save()
		else:
			form = forms.NeedsAttentionForm(request.POST, instance=es)
		context['attentionform'] = form
		context['matchform'] = forms.ExamScribbleMatchRobustForm(\
					user = request.user, examscribble = es)
		context['matchurl'] = "/helium/match-papers/%d/" %exam.id

		if es.needs_attention:
			messages.warning(request, "This exam scribble needs administrator attention. "
			"Reason: " + es.needs_attention)

	context['gradeform'] = forms.ExamGradingRobustForm(
			user = request.user,
			entity = entity,
			exam = exam,
			problems = exam.problem_set.all(),
			show_god = True)
	context['gradeurl'] = "/helium/old-grader/exam/%d/" %exam.id
	return render(request, "view-paper.html", context)

@staff_member_required
def view_conflicts_all(request):
	columns, table = _get_vtable(request, He.models.Verdict.objects\
			.filter(is_valid=False, problem__exam__is_ready = True) )
	context = {'columns' : columns, 'table' : table, 'pagetitle' : 'All Grading Conflicts'}
	return render(request, "table-only.html", context)
@staff_member_required
def view_conflicts_own(request):
	columns, table = _get_vtable(request, He.models.Verdict.objects\
			.filter(is_valid=False, problem__exam__is_ready = True,
				evidence__user = request.user) )
	context = {'columns' : columns, 'table' : table, 'pagetitle' : 'Own Grading Conflicts'}
	return render(request, "table-only.html", context)

## AJAX HOOKS
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
	scribble.last_sent_time = None
	scribble.save()
	return HttpResponse("OK", content_type="text/plain")
@staff_member_required
@require_POST
def ajax_next_scan(request):
	"""POST arguments: num_to_load, problem_id.
	RETURN: list of (scribble id, scribble url, examscribble id, verdict id)"""

	problem_id = int(request.POST['problem_id'])
	if problem_id == 0: return
	problem = He.models.Problem.objects.get(id=problem_id)
	n = int(request.POST['num_to_load'])

	scribbles = He.models.ProblemScribble.objects.filter(
			verdict__problem=problem, verdict__is_done=False)
	scribbles = scribbles.exclude(verdict__evidence__user = request.user)
	# wait 10 seconds before giving out the same scribble again
	scribbles = scribbles.exclude(last_sent_time__gte = time.time() - 10)

	ret = []
	for ps in scribbles[0:n]:
		ps.last_sent_time = time.time()
		ps.save()
		ret.append([ps.id, ps.prob_image.url, ps.examscribble.id, ps.verdict.id])
	if len(ret) < n: # didn't finish
		ret.append([0, DONE_IMAGE_URL, 0, 0])
	return HttpResponse( json.dumps(ret), content_type = 'application/json' )

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

## PROGRESS REPORTS
@staff_member_required
def progress_problems(request):
	"""Generates a table of how progress grading the problem is going."""
	main_queryset = He.models.Verdict.objects.order_by()\
			.values('problem_id', 'is_valid', 'is_done')\
			.annotate(count = Count('id'))

	results = collections.defaultdict(dict) # problem_id -> category -> count
	for query_d in main_queryset:
		problem_id = query_d['problem_id']
		if query_d['is_valid'] is False:
			category = "Conflict"
		elif query_d['is_valid'] is True and query_d['is_done'] is True:
			category = "Done"
		elif query_d['is_valid'] is True and query_d['is_done'] is False:
			category = "Pending"
		results[problem_id][category] = query_d['count']

	table = []
	columns = ['Problem', 'Done', 'Pending', 'Conflict']

	for problem in He.models.Problem.objects.all():
		problem_info = results.get(problem.id, None) # category -> count
		if problem_info is None: continue

		tr = collections.OrderedDict()
		tr['Problem']  = str(problem)
		tr['Done']     = problem_info.get("Done", 0)
		tr['Pending']  = problem_info.get("Pending", 0)
		tr['Conflict'] = problem_info.get("Conflict", 0)
		table.append(tr)

	context = {'columns' : columns, 'table' : table, 'pagetitle' : 'Grading Progress'}
	return render(request, "table-only.html", context)
@staff_member_required
def progress_scans(request):
	"""Generates a table showing how quickly the scans are being matched for a problem."""

	main_queryset = He.models.ExamScribble.objects.order_by()\
			.filter(exam__is_ready=True, exam__is_scanned=True)\
			.values('exam_id').annotate(
					done_count = Count('entity_id'),
					total_count = Count('id'))

	results = {}
	for query_d in main_queryset:
		exam_id = query_d['exam_id']
		results[exam_id] = {
				'Done': query_d['done_count'],
				'Left': query_d['total_count'] - query_d['done_count'],
				}

	table = []
	columns = ['Exam', 'Done', 'Left']

	for exam in He.models.Exam.objects.filter(is_ready=True, is_scanned=True):
		exam_info = results.get(exam.id, None) # category -> count
		if exam_info is None: continue

		tr = collections.OrderedDict()
		tr['Exam'] = str(exam)
		tr['Done'] = exam_info['Done']
		tr['Left'] = exam_info['Left']
		table.append(tr)

	context = {'columns' : columns, 'table' : table, 'pagetitle' : 'Scans Progress'}
	return render(request, "table-only.html", context)

## ESTIMATION CALC
@staff_member_required
def estimation_calc(request):
	"""This is a calculator for guts estimation problems."""
	scoring_fns = He.models.GutsScoreFunc.objects.all()
	return render(request, "estimation-calc.html", {'scoring_fns' : scoring_fns})

## SCAN UPLOAD AND TABLES
@staff_member_required
def upload_scans(request):
	"""Uploading scans happens here. Uses the image library."""
	if request.method == "POST":
		form = forms.UploadScanForm(request.POST, request.FILES)
		if form.is_valid():
			pdf_file = request.FILES['pdf']
			pdf_name = pdf_file.name
			exam = form.cleaned_data['exam']
			if not pdf_name.endswith(".pdf") and not pdf_name.endswith(".PDF"):
				messages.error(request, "File must end with .pdf or .PDF.")
			elif He.models.EntirePDFScribble.objects.filter(name = pdf_name).exists():
				messages.error(request, "PDF with name %s was already uploaded. "\
						"No action taken." % pdf_name)
			else:
				pdfscribble = He.models.EntirePDFScribble(name = pdf_name, exam = exam)
				pdfscribble.save()
				def target_function():
					sheets = scanimage.get_answer_sheets(pdf_file, filename = pdf_name)
					for sheet in sheets:
						es = He.models.ExamScribble(
								pdf_scribble = pdfscribble,
								exam = exam,
								full_image = sheet.get_full_file(),
								name_image = sheet.get_name_file())
						es.save()
						n = 0
						for prob_img in sheet.get_problem_files():
							n += 1
							es.createProblemScribble(n, prob_img)
					pdfscribble.is_done = True
					pdfscribble.save()
				threader.run_async(target_function, name = "upload_scans")
				messages.success(request, "PDF %s is OK, now processing" %pdf_name)
	else:
		form = forms.UploadScanForm()
	return render(request, "upload-scans.html", {'form' : form})

@staff_member_required
def view_pdf_redir(request):
	return _redir_obj_id(request, 'pdf', forms.PDFSelectForm)
@staff_member_required
def view_pdf(request, pdfscribble_id):
	"""This shows all pages in a PDF file"""
	pdfscribble = He.models.EntirePDFScribble.objects.get(id = int(pdfscribble_id))
	table = []
	columns = ['Page', 'Thumbnail', 'Entity', 'Open']
	n = 0
	for examscribble in He.models.ExamScribble.objects\
			.filter(pdf_scribble = pdfscribble):
		n += 1
		tr = collections.OrderedDict()
		tr['Page'] = n
		tr['Thumbnail'] = '<img class="thumbnail" src="%s" />' \
				% examscribble.name_image.url
		tr['Entity'] = examscribble.entity or "(Not Matched)"
		tr['Open'] = '<a href="/helium/view-paper/scan/%d">Open</a>' % examscribble.id
		table.append(tr)
	context = {'columns' : columns, 'table' : table,
			'pagetitle' : '%s (%s)' %(pdfscribble, pdfscribble.exam)}
	return render(request, "table-only.html", context)

## SCORE REPORTS
def _report(num_show = None, num_named = None, zero_pad = True,
		show_indiv_alphas = True, show_team_sum_alphas = True, show_hmmt_sweepstakes = True):
	"""Explanation of potions:
	num_show: Display only the top N entities
	num_named: Suppress the names of entities after rank N
	The other booleans are self explanatory."""

	output = '<!DOCTYPE html>' + "\n"
	output += '<html><head></head><body>' + "\n"
	output += '<pre style="font-family:Consolas,Monaco,Lucida Console,Liberation Mono,'\
			'DejaVu Sans Mono,Bitstream Vera Sans Mono,Courier New, monospace;">' + "\n"
	output += INIT_TEXT_BANNER + "\n\n"

	# Do this query once, we'll need it repeatedly
	mathletes = list(He.models.Entity.mathletes.all())
	teams = list(He.models.Entity.teams.all())


	# GET ALL SCORES NOW
	# Query through all verdicts, grouping by exam by problem
	# exam_id -> entity_id -> score list
	all_verdicts_dict = {}
	for exam in He.models.Exam.objects.all():
		all_verdicts_dict[exam.id] = collections.defaultdict(list)

	for v_dict in He.models.Verdict.objects.all()\
			.order_by('problem__problem_number')\
			.values('problem__exam_id', 'problem__weight',\
			'problem__allow_partial', 'entity_id', 'score'):
		exam_id, entity_id, score = v_dict['problem__exam_id'], v_dict['entity_id'], v_dict['score']
		if score is not None:
			if not v_dict['problem__allow_partial']: # all-or-nothing
				all_verdicts_dict[exam_id][entity_id].append(score * v_dict['problem__weight'])
			else:
				all_verdicts_dict[exam_id][entity_id].append(score)

	## Individual Results
	if show_indiv_alphas:
		output += presentation.RP_alphas().get_table("Overall Individuals (Alphas)", \
				num_show = num_show, num_named = num_named)
	output += "\n"

	indiv_exams = He.models.Exam.objects.filter(is_indiv=True)
	for exam in indiv_exams:
		rp = presentation.RP_exam(mathletes, all_verdicts_dict[exam.id])
		output += rp.get_table(heading = unicode(exam), \
				num_show = num_show, num_named = num_named, zero_pad = zero_pad)
	output += "\n"

	## Team Results
	team_exams = He.models.Exam.objects.filter(is_indiv=False)
	if show_hmmt_sweepstakes:
		team_exam_scores = collections.defaultdict(list) # unicode(team) -> list of scores

	for exam in team_exams:
		rp = presentation.RP_exam(teams, all_verdicts_dict[exam.id])
		output += rp.get_table(heading = unicode(exam), \
				num_show = num_show, num_named = num_named, zero_pad = zero_pad,
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
	# TODO optimize this part as well
	if show_team_sum_alphas:
		rp = presentation.RP_alpha_sums(mathletes, teams)
		output += rp.get_table(heading = "Team Individual Aggregate", \
				num_show = num_show, num_named = num_named, zero_pad = zero_pad)
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
				num_show = None, num_named = None,
				float_string = "%7.2f", int_string = "%7d")

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
	return _report(zero_pad = False)
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
	threader.run_async(target_function, name = command_name)
	return HttpResponse("Command %s started" % command_name, content_type="text/plain")

# vim: fdm=indent foldnestmax=1
