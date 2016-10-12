from django import forms
import django.utils.safestring
import helium as He
import logging

class MathleteModelChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, mathlete):
		return mathlete.name

class ProblemScanSelectForm(forms.Form):
	"""Lets you pick a problem marked as ready for grading"""
	problem = forms.ModelChoiceField(
			label = "Read scans for problem",
			queryset = He.models.Problem.objects\
					.filter(exam__is_ready=True, exam__is_scanned=True))

class ExamSelectForm(forms.Form):
	"""Picks an exam marked as ready for grading"""
	exam = forms.ModelChoiceField(
			label = "Select exam",
			queryset = He.models.Exam.objects.filter(is_ready=True))
class ExamScanSelectForm(forms.Form):
	"""Picks an exam marked as ready for grading and marked for scanning."""
	exam = forms.ModelChoiceField(
			label = "Read scans for exam",
			queryset = He.models.Exam.objects.filter(is_ready=True, is_scanned=True))

# The following forms are ROBUST in the sense that
# the form.clean() method will actually do the processing work
# of updating the models

class ExamGradingRobustForm(forms.Form):
	"""Creates a form for the old-style grader.
	Note this form is *robust*: on submission (actually in the clean() method),
	it will actually submit the changes to the database"""
	def __init__(self, exam, user, *args, **kwargs):
		if not user.is_staff:
			raise ValueError("User is not staff")
		super(forms.Form, self).__init__(*args, **kwargs)
		problems = exam.problems.all()
		self.exam = exam
		self.user = user
		self.problems = list(problems)
		if self.exam.is_indiv:
			self.fields['entity'] = MathleteModelChoiceField(\
					queryset = He.models.Entity.mathletes.all())
		else:
			self.fields['entity'] = forms.ModelChoiceField(\
					queryset = He.models.Entity.teams.all())
		for problem in problems:
			n = problem.problem_number
			kwargs = {
					'label' : unicode(problem),
					# 'widget' : forms.TextInput,
					'required' : False,
					'min_value' : 0,
					}
			if not problem.allow_partial:
				kwargs['max_value'] = 1
				kwargs['help_text'] = "Input 0 or 1."
			elif problem.weight is not None:
				kwargs['max_value'] = problem.weight
				kwargs['help_text'] = "Weight is %d." %problem.weight
			else:
				kwargs['help_text'] = ""
			if problem.answer.strip() != '':
				kwargs['help_text'] = 'Answer is %s. ' %problem.answer + kwargs['help_text']
			self.fields['p' + str(n)] = forms.IntegerField(**kwargs)
		self.fields['force'] = forms.BooleanField(
				label = 'Override',
				required = False,
				help_text = "Use this to override a merge conflict.")
	def clean(self):
		if not self.user.is_staff:
			raise ValueError("User is not staff")
		data = super(ExamGradingRobustForm, self).clean()
		if not self.is_valid():
			return # didn't pass first validation, don't do queries

		entity = data['entity']
		num_graded = 0
		for problem in self.problems:
			field_name = 'p' + str(problem.problem_number)
			v, _ = He.models.Verdict.objects.get_or_create(entity=entity, problem=problem)
			user_score = data.get(field_name, None)
			if user_score is None:
				continue
			if v.score is not None and user_score != v.score and data['force'] is False:
				previous_graders = [unicode(e.user) for e in v.evidence_set.all()]
				if len(previous_graders) > 1 or previous_graders[0] != unicode(self.user):
					self.add_error(field_name,
							"Conflict: Database has score %d (entered by %s)"
							% (v.score, ', '.join(previous_graders)))
					continue
			v.submitEvidence(user = self.user, score = user_score)
			num_graded += 1
		return { 'num_graded' : num_graded, 'entity' : entity }

class ExamScribbleMatchRobustForm(forms.Form):
	"""Creates a form for matching scribbles to teams/mathletes.
	Note this form is *robust*: on submission (actually in the clean() method),
	it will actually submit the changes to the database"""
	def __init__(self, examscribble, user, *args, **kwargs):
		super(forms.Form, self).__init__(*args, **kwargs)
		self.examscribble = examscribble
		self.user = user
		self.exam = examscribble.exam

		if self.exam.is_indiv:
			self.fields['entity'] = MathleteModelChoiceField(\
					queryset = He.models.Entity.mathletes.all())
		else:
			self.fields['entity'] = forms.ModelChoiceField(\
					queryset = He.models.Entity.teams.all())

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
					help_text = "Super-users can use this to cause havoc.")

	def clean(self):
		data = super(ExamScribbleMatchRobustForm, self).clean()
		entity = data['entity']

		# Now for each attached ProblemScribble...
		# check if it's okay to update
		bad_v = self.examscribble.checkConflictVerdict(
				entity, purge = data.get('force', False))
		if bad_v is None:
			data['entity'] = entity
			self.examscribble.assign(entity)
			# Now update all the verdicts attached to the exam scribble
		else:
			admin_url = "/admin/helium/verdict/" + str(bad_v.id) + "/change/"
			self.add_error(None, django.utils.safestring.mark_safe(
					'A verdict already exists for a problem/user pair. '
					'Something is wrong! Consult '
					'<a href="%s">%s</a>. ' %(admin_url, bad_v)))
		return data

# vim: fdm=indent foldnestmax=2
