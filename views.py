"""
HELIUM 2
(c) 2017 Evan Chen
See LICENSE.txt for details.

views.py

This is the massive views.py.

CONVENTION: Name of view function is always the URL
with all dashes and slashes replaced by underscores

This file is divided into roughly a few parts:

## Grading views: for example
* The classical grader (old_grader_*), grade by name and test/problem
* The interface matching papers to students (fast_match)
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

## Task views
view_task, which lets you view the status of an async task

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
from django.utils.html import escape
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
import scanimage
import threader
from presentation import ResultPrinter as RP
import presentation
import sheetapi

DONE_IMAGE_URL = static('img/done.jpg')

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

## VIEWS FOR FAST SCAN MATCH
@staff_member_required
def fast_match_redir(request, attention=False):
	return _redir_obj_id(request,
			key = 'exam',
			form_type = forms.ExamScanSelectForm)
@staff_member_required
def fast_match(request, exam_id, attention=False):
	"""The fast match system.  Most of the work is in the template.

	Normally the boolean attention is False,
	meaning that scribbles marked as "needing attention" will not be shown.
	However, if True then instead *only* scribbles needing attention will be displayed.
	"""
	show_attention = int(bool(attention)) # 0 or 1
	exam = He.models.Exam.objects.get(id=exam_id)
	takers = exam.takers.all()
	field = forms.EntityModelChoiceField(queryset = takers)
	widgetHTML = field.widget.render(name = "entity", value = "", attrs = {'id' : 'id_entity'})
	context = {'exam' : exam, 'entities' : takers, 'widgetHTML' : widgetHTML, 'show_attention' : show_attention}
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
	columns = ['Entity', 'Problem', 'Score', 'Size']
	for verdict in verdicts:
		tr = collections.OrderedDict()
		tr['Entity'] = verdict.entity
		tr['Problem'] = verdict.problem
		tr['Score'] = verdict.score if verdict.score is not None else "?"
		tr['Size'] = "<a href=\"/helium/view-verdict/%d/\">%d</a>" \
				% (verdict.id, verdict.evidence_set.count())
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
		context['columns'] = ['Exam', 'Reason', 'Entity']
		table = []
		# List scribbles needing attention
		for es in He.models.ExamScribble.objects.exclude(needs_attention=u''):
			tr = collections.OrderedDict()
			tr['Exam'] = '<a href="/helium/view-paper/scan/%d">%s</a>' %(es.id, es.exam)
			tr['Reason'] = es.needs_attention
			tr['Entity'] = es.entity
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
	if request.method == 'POST': # submitted an update here
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
		context['matchform'] = form
		es.refresh_from_db()
	elif es is not None:
		context['matchform'] = forms.ExamScribbleMatchRobustForm(\
					user = request.user, examscribble = es)
		context['matchurl'] = "/helium/match-papers/%d/" %exam.id

	if es and es.needs_attention:
		messages.warning(request,
				"This exam scribble needs administrator attention.<br> "
				"Reason: " + es.needs_attention)
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
### Ajax for scan grader
@staff_member_required
@require_POST
def ajax_submit_scan(request):
	"""POST arguments: examscribble_id, score. RETURN: nothing useful"""
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
	pos = int(request.POST['pos'])

	scribbles = He.models.ProblemScribble.objects.filter(
			verdict__problem=problem, verdict__is_done=False)
	# Prevent giving out scribbles that need attention
	scribbles = scribbles.filter(examscribble__needs_attention='')
	# Cool-down and position
	scribbles = scribbles.exclude(verdict__evidence__user = request.user)\
			.filter(id__gt = pos).exclude(last_sent_time__gte = time.time() - 10)
			# cooldown, pos

	ret = []
	for ps in scribbles[0:n]:
		ps.last_sent_time = time.time()
		ps.save()
		ret.append([ps.id, ps.prob_image.url, ps.examscribble.id, ps.verdict.id])
	if len(ret) < n: # all done!
		ret.append([0, DONE_IMAGE_URL, 0, 0])
	return HttpResponse( json.dumps(ret), content_type = 'application/json' )

### Ajax for filling in classical grader
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

### Ajax for scan matcher
@staff_member_required
@require_POST
def ajax_submit_match(request):
	"""POST arguments: examscribble_id, entity_id, attention
	RETURN: nothing useful"""
	try:
		examscribble_id = int(request.POST['examscribble_id'])
	except ValueError:
		return HttpResponse("No such exam scribble", content_type="text/plain")
	es = He.models.ExamScribble.objects.get(id = examscribble_id)

	if request.POST['attention']:
		es.needs_attention = escape(request.POST['attention'].strip())
		es.unassign()
		return HttpResponse("Silly children", content_type="text/plain")
	else:
		es.needs_attention = ''
		es.save()

	entity_id = int(request.POST['entity_id'])
	entity = es.exam.takers.get(id = entity_id)
	bad_v = es.checkConflictVerdict(entity)
	es.last_sent_time = None # reset timer, not that it matters
	if bad_v is not None:
		es.needs_attention = "%s matched to %s,\
				<a href=\"/helium/view-verdict/%d\">conflict</a>"\
				%(request.user, entity, bad_v.id)
		es.unassign() # which should save too
		# es.save() # done by es.assign
		return HttpResponse("Conflict, marked for attention", content_type="text/plain")
	else:
		es.assign(entity)
		return HttpResponse("OK", content_type="text/plain")
@staff_member_required
@require_POST
def ajax_next_match(request):
	"""POST arguments: num_to_load, exam_id, show_attention, pos (an ID)
	RETURN: list of (examscribble id, examscribble url, attention reason)"""

	exam_id = int(request.POST['exam_id'])
	if exam_id == 0: return
	exam = He.models.Exam.objects.get(id=exam_id)
	n = int(request.POST['num_to_load'])
	pos = int(request.POST['pos'])

	if int(request.POST['show_attention']) == 1:
		scribbles = He.models.ExamScribble.objects.exclude(needs_attention=u'')
	else:
		scribbles = He.models.ExamScribble.objects\
				.filter(entity__isnull=True, needs_attention=u'')\
				.exclude(last_sent_time__gte = time.time() - 20) # cooldown
	scribbles = scribbles.filter(id__gt = pos)

	ret = []
	for es in scribbles[0:n]:
		es.last_sent_time = time.time()
		es.save()
		ret.append([es.id, es.name_image.url, es.needs_attention or ''])
	if len(ret) < n: # all done!
		ret.append([0, DONE_IMAGE_URL])
	return HttpResponse( json.dumps(ret), content_type = 'application/json' )

### Ajax for task checkup
@staff_member_required
@require_POST
def ajax_task_query(request):
	"""POST arguments: task_id
	RETURN: (status, text)
		status: OK if done, FAIL if failed, None otherwise"""
	task_id = int(request.POST['task_id'])
	task_record = He.models.ThreadTaskRecord.objects.get(id=task_id)
	if task_record.status is True:
		status = "OK"
	elif task_record.status is False:
		status = "FAIL"
	elif task_record.status is None:
		status = None
	output = task_record.output or ""
	return HttpResponse( json.dumps([status, output]), content_type='application/json' )

@staff_member_required
def view_task(request, task_id):
	task_record = He.models.ThreadTaskRecord.objects.get(id=task_id)
	context = {"task" : task_record}
	return render(request, "view-task.html", context)

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
				threader.run_async(target_function, user = request.user, name = "upload_scans")
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
	columns = ['Page', 'Thumbnail', 'Entity']
	n = 0
	for examscribble in He.models.ExamScribble.objects\
			.filter(pdf_scribble = pdfscribble):
		n += 1
		tr = collections.OrderedDict()
		tr['Page'] = '<a href="/helium/view-paper/scan/%d">#%d</a>' % (examscribble.id, n)
		tr['Thumbnail'] = '<img class="thumbnail" src="%s" />' \
				% examscribble.name_image.url
		tr['Entity'] = examscribble.entity or "(Not Matched)"
		table.append(tr)
	context = {'columns' : columns, 'table' : table,
			'pagetitle' : '%s (%s)' %(pdfscribble, pdfscribble.exam)}
	return render(request, "table-only.html", context)

## SCORE REPORTS
@staff_member_required
def reports_short(request):
	return HttpResponse(presentation.HMMT_text_report(num_show=10), content_type="text/html")
@staff_member_required
def reports_extended(request):
	return HttpResponse(presentation.HMMT_text_report(num_named=50), content_type="text/html")
@user_passes_test(lambda u: u.is_superuser)
def reports_full(request):
	return HttpResponse(presentation.HMMT_text_report(zero_pad=False), content_type="text/html")
def reports_teaser(request):
	"""ACCESSIBLE TO NON-STAFF!"""
	return HttpResponse(presentation.HMMT_text_report(num_show=15, num_named=0), content_type="text/html")

@user_passes_test(lambda u: u.is_superuser)
def reports_spreadsheet(request):
	sheets = collections.OrderedDict() # sheet name -> rows
	all_rows = presentation.get_score_rows()

	## Individual Results
	for exam in He.models.Exam.objects.all():
		sheets[unicode(exam)] = RP(all_rows[exam.name]).get_sheet()
	sheets["Indiv"] = RP(all_rows["Individual Overall"]).get_sheet()
	sheets["Aggr"] = RP(all_rows["Team Aggregate"]).get_sheet()
	sheets["Sweeps"] = RP(all_rows["Sweepstakes"]).get_sheet()

	odf = sheetapi.get_odf_spreadsheet(sheets)
	response = HttpResponse(odf,\
			content_type="application/vnd.oasis.opendocument.spreadsheet")
	response['Content-Disposition'] = 'attachment; filename=scores-%s.ods' \
			% time.strftime("%Y%m%d-%H%M%S")
	return response

@staff_member_required
def reports_awards(request):
	queryset = He.models.ScoreRow.objects.filter(rank__lte = 10) # top 10 each
	awards_tex= presentation.HMMT_awards(queryset)
	r = HttpResponse(content_type='application/x-tex')
	r.write(awards_tex)
	r['Content-Disposition'] = 'attachment; filename=awards-%s.tex' \
			% time.strftime("%Y%m%d-%H%M%S")
	return r

## MANAGEMENT
@user_passes_test(lambda u: u.is_superuser)
def run_management(request, command_name):
	"""Starts a thread which runs a specified management command"""
	def target_function():
		django.core.management.call_command(command_name)
	task_id = threader.run_async(target_function, user = request.user, name = command_name)
	return HttpResponseRedirect("/helium/view-task/%d" %task_id)

# vim: fdm=indent foldnestmax=1
