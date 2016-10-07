from django import forms
import helium as He
from registration.current import TEAMS, MATHLETES
import logging

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
    def __init__(self, exam, user, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        problems = He.models.Problem.objects.filter(exam=exam)

        self.exam = exam
        self.user = user
        self.problems = problems

        if self.exam.is_indiv:
            self.fields['mathlete'] = forms.ModelChoiceField(\
                    queryset = MATHLETES.all())
        else:
            self.fields['team'] = forms.ModelChoiceField(\
                    queryset = TEAMS.all())
        
        logging.warn(self.problems)
        for problem in sorted(self.problems, key = lambda _ : _.problem_number):
            n = problem.problem_number
            kwargs = {
                    'label' : unicode(problem),
                    'widget' : forms.TextInput,
                    'required' : False,
                    'min_value' : 0,
                    # 'help_text' : "Answer is %s" %problem.answer,
                    }
            if not problem.allow_partial:
                kwargs['max_value'] = 1
                kwargs['help_text'] = "Input 0 or 1"
            elif hasattr(problem, "weight"):
                kwargs['max_value'] = problem.weight
                kwargs['help_text'] = "Input an integer from 0 to %d" %problem.weight
            else:
                kwargs['help_text'] = "Input a nonnegative integer"

            self.fields['p' + str(n)] = forms.IntegerField(**kwargs)

        self.fields['force'] = forms.BooleanField(
                label = 'Override',
                required = False)

    def clean(self):
        # without "force", throw an error every time we get a bad verdict
        data = super(ExamGradingForm, self).clean()

        if self.exam.is_indiv:
            if not data.has_key('mathlete'):
                # NOT NEEDED: validation will do this for us
                # self.add_error('mathlete', 'No mathlete specified!?')
                return
            else:
                whom = data['mathlete']
        if not self.exam.is_indiv and not data.has_key('team'):
            if not data.has_key('team'):
                # NOT NEEDED: validation will do this for us
                # self.add_error('team', 'No team specified!?')
                return
            else:
                whom = data['team']

        num_graded = 0
        for problem in self.problems:
            field_name = 'p' + str(problem.problem_number)

            # Get verdict corresponding to student/team + problem
            if self.exam.is_indiv: # indiv exam
                v, _ = He.models.Verdict.objects.get_or_create(
                        mathlete=data['mathlete'], problem=problem)
            else: # team exam
                v, _ = He.models.Verdict.objects.get_or_create(
                        team = data['team'], problem=problem)

            user_score = data.get(field_name, None)
            if user_score is None:
                continue
            if v.score is not None:
                if user_score != v.score and data['force'] is False:
                    self.add_error(field_name,
                            "Conflicting score for %s (database has score %d)" \
                            % (problem, v.score))
                    continue
            v.submitEvidence(user = self.user, score = user_score)
            num_graded += 1
        return { 'num_graded' : num_graded, 'whom' :  whom}

# vim: expandtab fdm=indent foldnestmax=1
