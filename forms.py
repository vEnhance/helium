"""
HELIUM
(c) 2016 Evan Chen
See LICENSE.txt for details.

forms.py

These are automatic Django forms used in the templates and throughout.
The first few are pretty self-explanatory.

The ROBUST forms are interesting in that they save changes to database
in the clean() method (not sure if this is the right thing to do).
"""


from django import forms
import django.utils.safestring
import helium as He

class ProblemSelectForm(forms.Form):
	"""Picks a problem marked ready for grading"""
	problem = forms.ModelChoiceField(
			label = "Select problem",
			queryset = He.models.Problem.objects\
					.filter(exam__is_ready=True))
class ProblemNoScanSelectForm(forms.Form):
	"""Picks a problem marked ready for grading and NOT scanned"""
	problem = forms.ModelChoiceField(
			label = "Select non-scanned problem",
			queryset = He.models.Problem.objects\
					.filter(exam__is_ready=True, exam__is_scanned=False))
class ProblemScanSelectForm(forms.Form):
	"""Lets you pick a problem marked as ready for grading and scanned."""
	problem = forms.ModelChoiceField(
			label = "Read scans for problem",
			queryset = He.models.Problem.objects\
					.filter(exam__is_ready=True, exam__is_scanned=True))

class ExamSelectForm(forms.Form):
	"""Picks an exam marked as ready for grading"""
	exam = forms.ModelChoiceField(
			label = "Select exam",
			queryset = He.models.Exam.objects.filter(is_ready=True))
class ExamNoScanSelectForm(forms.Form):
	"""Picks an exam marked as ready for grading and NOT scanned."""
	exam = forms.ModelChoiceField(
			label = "Select non-scanned exam",
			queryset = He.models.Exam.objects.filter(is_ready=True, is_scanned=False))
class ExamScanSelectForm(forms.Form):
	"""Picks an exam marked as ready for grading and marked for scanning."""
	exam = forms.ModelChoiceField(
			label = "Read scans for exam",
			queryset = He.models.Exam.objects.filter(is_ready=True, is_scanned=True))

class EntityExamSelectForm(forms.Form):
	"""Picks any exam (even one not marked ready) and any entity"""
	exam = forms.ModelChoiceField(label = "Exam",
			queryset = He.models.Exam.objects.all())
	team = forms.ModelChoiceField(label = "Team", required = False,
			queryset = He.models.Entity.teams.all(),
			help_text = "Specify the team to look up. Ignored for individual exams.")
	mathlete = forms.ModelChoiceField(label = "Mathlete", required = False,
			queryset = He.models.Entity.mathletes.all(),
			help_text = "Specify the mathlete to look up. Ignored for team exams.")
	def clean(self):
		data = super(EntityExamSelectForm, self).clean()
		if not self.is_valid():
			return
		exam = data['exam']
		if exam.is_indiv is True:
			entity = data['mathlete']
			if entity is None:
				self.add_error('mathlete', "Need to specify mathlete for %s" %exam)
				return
		else:
			entity = data['team']
			if entity is None:
				self.add_error('team', "Need to specify team for %s" %exam)
				return
		self.cleaned_data['entity'] = entity

class UploadScanForm(forms.Form):
	"""Takes an exam and a PDF scan of several pages"""
	exam = forms.ModelChoiceField(
			label = "Exam",
			queryset = He.models.Exam.objects.filter(is_ready=True, is_scanned=True),
			help_text = "Please, please, PLEASE check this is right!")
	pdf = forms.FileField(label = "Upload PDF",
			help_text = "Note file names must be unique; "\
			"this is a safety feature to prevent accidental double submission.")

class NeedsAttentionForm(forms.ModelForm):
	"""A simple form which toggles whether a exam scribble needs attention."""
	class Meta:
		model = He.models.ExamScribble
		fields = ['needs_attention']

class PDFSelectForm(forms.Form):
	"""Selects a EntireScanPDF object"""
	pdf = forms.ModelChoiceField(
			label = "View PDF",
			queryset = He.models.EntirePDFScribble.objects.all())

# The following forms are ROBUST in the sense that
# the form.clean() method will actually do the processing work
# of updating the models


class ExamGradingRobustForm(forms.Form):
	"""Creates a form for the old-style grader.
	Note this form is *robust*: on submission (actually in the clean() method),
	it will actually submit the changes to the database.
	
	Exam, user, problems fields are self-explanatory.
	If the entity keyword is specified, self.fields['entity'] is removed and populated with that value
	show_force shows the force button
	show_god shows the God button
	"""
	def __init__(self, *args, **kwargs):
		self.exam = kwargs.pop('exam')
		self.user = kwargs.pop('user')
		self.problems = list(kwargs.pop('problems'))
		self.entity = kwargs.pop('entity', None)
		self.show_force = kwargs.pop('show_force', True)
		self.show_god = kwargs.pop('show_god', False)
		super(forms.Form, self).__init__(*args, **kwargs)
		if self.entity is not None:
			self.fields['entity'] = forms.ModelChoiceField(\
					queryset = He.models.Entity.objects.all(),
					initial = self.entity)
			self.fields['entity'].widget = forms.HiddenInput()
		elif self.exam.is_indiv:
			self.fields['entity'] = forms.ModelChoiceField(\
					queryset = He.models.Entity.mathletes.all())
		else:
			self.fields['entity'] = forms.ModelChoiceField(\
					queryset = He.models.Entity.teams.all())

		for problem in self.problems:
			n = problem.problem_number
			kwargs = {
					'label' : '%s [%s]' %(unicode(problem), round(problem.weight,2)),
					# 'widget' : forms.TextInput,
					'required' : False,
					'min_value' : 0,
					}
			if not problem.allow_partial:
				kwargs['max_value'] = 1
				kwargs['help_text'] = "Input 0 or 1."
			elif problem.weight is not None:
				kwargs['max_value'] = problem.weight
				kwargs['help_text'] = "Input score out of %s." %(problem.weight)
			else:
				kwargs['help_text'] = ""
			if problem.answer.strip() != '':
				kwargs['help_text'] = 'Answer is <span class="answer">%s</span>. ' \
						%problem.answer + kwargs['help_text']
			self.fields['p' + str(n)] = forms.IntegerField(**kwargs)
		self.fields['force'] = forms.BooleanField(
				label = 'Override',
				required = False,
				help_text = "Suppress warnings that you are going against the majority vote.")
		if self.show_god:
			self.fields['god_mode'] = forms.BooleanField(
					label = 'GOD Mode',
					required = False,
					help_text = "Enables GOD MODE for admins.")
	def clean(self):
		"""Return a num_graded, entity dictionary"""
		data = super(ExamGradingRobustForm, self).clean()
		if not self.is_valid():
			return # didn't pass first validation, don't do queries
		entity = self.entity or data['entity']
		num_graded = 0
		is_god = data.get('god_mode', False)
		is_forceful = is_god or data['force'] # is_god implies is_forceful

		for problem in self.problems:
			field_name = 'p' + str(problem.problem_number)
			v, _ = He.models.Verdict.objects.get_or_create(entity=entity, problem=problem)
			user_score = data.get(field_name, None)
			if user_score is None:
				continue
			if v.score is not None and user_score != v.score and not is_forceful:
				previous_graders = [unicode(e.user) for e in v.evidence_set.all()]
				if len(previous_graders) > 1 or previous_graders[0] != unicode(self.user):
					self.add_error(field_name,
							"Conflict: Database has score %d (entered by %s)"
							% (v.score, ', '.join(previous_graders)))
					continue
			v.submitEvidence(user = self.user, score = user_score, god_mode = is_god)
			num_graded += 1
		return { 'num_graded' : num_graded, 'entity' : entity }

class ExamScribbleMatchRobustForm(forms.Form):
	"""Creates a form for matching scribbles to teams/mathletes.
	Note this form is *robust*: on submission (actually in the clean() method),
	it will actually submit the changes to the database"""
	def __init__(self, *args, **kwargs):
		self.examscribble = kwargs.pop('examscribble')
		self.user = kwargs.pop('user')
		super(forms.Form, self).__init__(*args, **kwargs)
		self.exam = self.examscribble.exam

		if self.exam.is_indiv:
			self.fields['entity'] = forms.ModelChoiceField(\
					queryset = He.models.Entity.mathletes.all(),
					label = "Mathlete")
		else:
			self.fields['entity'] = forms.ModelChoiceField(\
					queryset = He.models.Entity.teams.all(),
					label = "Team")

		# TODO it would be nice if there was an easy way
		# to filter for mathletes / teams which aren't already matched
		# This seems too expensive / clunky.

		self.fields['examscribble_id'] = forms.IntegerField(\
				initial = self.examscribble.id,
				widget = forms.HiddenInput)

		if self.user.is_superuser:
			self.fields['force'] = forms.BooleanField(
					label = 'Override',
					required = False,
					help_text = "Super-users can use this to cause havoc. "\
							"Please avoid using unless you know what it does.")

	def clean(self):
		data = super(ExamScribbleMatchRobustForm, self).clean()
		if not self.is_valid():
			return
		entity = data['entity']

		# Now for each attached ProblemScribble...
		# check if it's okay to update
		bad_v = self.examscribble.checkConflictVerdict(
				entity, purge = data.get('force', False))
		if bad_v is None: # we are OK
			data['entity'] = entity
			self.examscribble.assign(entity)
			# Now update all the verdicts attached to the exam scribble
		else:
			target_url = "/helium/view-verdict/%d/" % bad_v.id
			self.add_error(None, django.utils.safestring.mark_safe(
					'A verdict already exists for a problem/user pair. '
					'Something is wrong! Consult '
					'<a href="%s">%s</a>. ' %(target_url, bad_v)))
		return data

# vim: fdm=indent foldnestmax=2
