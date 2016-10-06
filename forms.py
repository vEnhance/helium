from django import forms
import helium as He
from registration.current import TEAMS, MATHLETES

class ProblemSelectForm(forms.Form):
    """Lets you pick a problem marked as ready for grading"""
    problem = forms.ModelChoiceField(
            label = "Read scans for problem",
            queryset = He.models.Problem.objects.filter(exam__is_ready=True))

class ExamSelectForm(forms.Form):
    """Picks an exam marked as ready for grading"""
    exam = forms.ModelChoiceField(
            label = "Mark exams the old way",
            queryset = He.models.Exam.objects.filter(is_ready=True))

class ExamGradingForm(forms.Form):
    def __init__(self, exam, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        problems = He.models.Problem.objects.filter(exam=exam)

        if exam.is_indiv:
            self.fields['mathlete'] = forms.ModelChoiceField(\
                    queryset = MATHLETES.all())
        else:
            self.fields['team'] = forms.ModelChoiceField(\
                    queryset = TEAMS.all())
        
        for p in sorted(problems, key = lambda _ : _.problem_number):
            n = p.problem_number
            self.fields[p] = forms.IntegerField(\
                    label = unicode(p),
					widget = forms.TextInput,
					help_text = "Answer is %s" %p.answer)
