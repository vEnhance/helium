from django import forms
import helium as He

class ProblemScanForm(forms.Form):
	"""Lets you pick a problem marked as ready for grading"""
	problem = forms.ModelChoiceField(
			label = "Grade scan for problem",
			queryset = He.models.Problem.objects.filter(exam__is_ready=True))
