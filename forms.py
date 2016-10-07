from django import forms
import django.utils.safestring
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
            label = "Select exam",
            queryset = He.models.Exam.objects.filter(is_ready=True))

class ExamGradingRobustForm(forms.Form):
    """Creates a form for the old-style grader.
    Note this form is *robust*: on submission (actually in the clean() method),
    it will actually submit the changes to the database"""
    def __init__(self, exam, user, *args, **kwargs):
        if not user.is_staff:
            raise ValueError("User is not staff")
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
                required = False,
                help_text = "Use this to override a merge conflict")

    def clean(self):
        if not self.user.is_staff:
            raise ValueError("User is not staff")
        data = super(ExamGradingRobustForm, self).clean()
        if not self.is_valid():
            return # didn't pass first validation, don't do queries

        whom = data['mathlete'] if self.exam.is_indiv else data['team']
        num_graded = 0
        for problem in self.problems:
            field_name = 'p' + str(problem.problem_number)
            v, _ = He.models.query_verdict('get_or_create', whom, problem)
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

class ExamScribbleMatchRobustForm(forms.Form):
    """Creates a form for matching scribbles to teams/mathletes.
    Note this form is *robust*: on submission (actually in the clean() method),
    it will actually submit the changes to the database"""
    def __init__(self, examscribble, user, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        self.examscribble = examscribble
        self.user = user
        self.exam = examscribble.exam

        if self.examscribble.exam.is_indiv:
            self.fields['mathlete'] = forms.ModelChoiceField(\
                    queryset = MATHLETES.all())
        else:
            self.fields['team'] = forms.ModelChoiceField(\
                    queryset = TEAMS.all())
        # TODO it would be nice if there was an easy way
        # to filter for mathletes / teams which aren't already matched

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
        if self.exam.is_indiv:
            if not data.has_key('mathlete'): return
            else: whom = data['mathlete']
        if not self.exam.is_indiv and not data.has_key('team'):
            if not data.has_key('team'): return
            else: whom = data['team']
        data['whom'] = whom

        # Now for each attached ProblemScribble...
        # check if it's okay to update
        for ps in self.examscribble.problemscribble_set.all():
            verdict = ps.verdict
            problem = verdict.problem
            try: # search for conflicts
                bad_v = He.models.query_verdict("get", whom, problem)
            except He.models.Verdict.DoesNotExist: 
                pass
            else: # UH-OH, there's already a verdict attached
                if not data.get('force', False): # we can just fail and leave now
                    admin_url = "/admin/helium/verdict/" + str(bad_v.id) + "/change/"
                    self.add_error(None, django.utils.safestring.mark_safe(
                            'A verdict already exists for a problem/user pair. '
                            'Something is very wrong. Consult '
                            '<a href="%s">%s</a>. ' %(admin_url, bad_v)))
                    return data
                else: # forcefully grab all evidence form v then delete it
                    for e in bad_v.evidence_set.all():
                        if e.user == self.user and He.models.Evidence.objects.filter\
                                (verdict=verdict, user=self.user).exists():
                            # geez this is so bad
                            logging.warn("Deleting " + str(e.id) + " = " + str(e))
                            e.delete()
                        else:
                            e.verdict = verdict
                            e.save()
                    logging.warn("Deleting " + str(bad_v.id) + " = " + str(bad_v))
                    bad_v.delete()
            verdict.updateDecisions()
        self.examscribble.assign(whom) # Now update all the verdicts attached to the exam scribble
        return data

# vim: expandtab fdm=indent foldnestmax=2
