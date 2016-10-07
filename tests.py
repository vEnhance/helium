from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

import helium as He
import registration.models as reg

class GradingTestCase(TestCase):
    def setUp(self):
        # HMMT 2016 Scripts Team whee
        self.evan   = User.objects.create_user(username='evan', password='.')
        self.calvin = User.objects.create_user(username='calvin', password='.')
        self.miguel = User.objects.create_user(username='miguel', password='.')
        self.kevin  = User.objects.create_user(username='kevin', password='.')

        self.exam   = He.models.Exam.objects.create(name="Sample Individual Exam",\
                is_indiv=True, is_alg_scoring=True, is_ready=True)
        self.prob1  = He.models.Problem.objects.create(exam = self.exam, problem_number = 1)
        self.prob2  = He.models.Problem.objects.create(exam = self.exam, problem_number = 2)
        self.prob3  = He.models.Problem.objects.create(exam = self.exam, problem_number = 3)

        self.verdict = He.models.Verdict.objects.create(problem=self.prob1)

        # Let's make a black mop team
        self.mop    = reg.Organization.objects.create(name = "MOP",
                address="Lincoln, NE", coach = self.evan)
        self.team   = reg.TeamFeb.objects.create(name = "Black MOP 1",
                shortname = "MOP K1", organization = self.mop)
        self.mathlete = reg.MathleteFeb.objects.create(
                first = "Example", last = "Student",
                organization = self.mop, team = self.team)

    def test_doublegrade_1(self):
        self.assertEqual(self.verdict.score, None)

        # Calvin submits a score of 7
        self.verdict.submitEvidence(self.calvin, 7)
        self.assertEqual(self.verdict.score, 7)
        self.assertEqual(self.verdict.is_valid, True)
        self.assertEqual(self.verdict.is_done, False)
        
        # Kevin submits a score of 5
        self.verdict.submitEvidence(self.kevin, 5)
        self.assertEqual(self.verdict.score, None)
        self.assertEqual(self.verdict.is_valid, False)
        self.assertEqual(self.verdict.is_done, False)

        # Miguel submits a score of 7
        self.verdict.submitEvidence(self.miguel, 7)
        self.assertEqual(self.verdict.score, None)
        self.assertEqual(self.verdict.is_valid, False)
        self.assertEqual(self.verdict.is_done, False)

        # Evan submits a score of 7
        self.verdict.submitEvidence(self.evan, 7)
        self.assertEqual(self.verdict.score, 7)
        self.assertEqual(self.verdict.is_valid, True)
        self.assertEqual(self.verdict.is_done, True)

    def test_doublegrade_2(self):
        self.assertEqual(self.verdict.score, None)

        # Calvin submits a score of 7
        self.verdict.submitEvidence(self.calvin, 7)
        self.assertEqual(self.verdict.score, 7)
        self.assertEqual(self.verdict.is_valid, True)
        self.assertEqual(self.verdict.is_done, False)
        
        # Kevin submits a score of 5
        self.verdict.submitEvidence(self.kevin, 5)
        self.assertEqual(self.verdict.score, None)
        self.assertEqual(self.verdict.is_valid, False)
        self.assertEqual(self.verdict.is_done, False)

        # Evan submits a score of 0 in God mode
        self.verdict.submitEvidence(self.evan, 0, god_mode = True)
        self.assertEqual(self.verdict.score, 0)
        self.assertEqual(self.verdict.is_valid, True)
        self.assertEqual(self.verdict.is_done, True)

    def test_doublegrade_3(self):
        self.assertEqual(self.verdict.score, None)

        # Calvin submits a score of 7
        self.verdict.submitEvidence(self.calvin, 7)
        self.assertEqual(self.verdict.score, 7)
        self.assertEqual(self.verdict.is_valid, True)
        self.assertEqual(self.verdict.is_done, False)
        
        # Kevin submits a score of 7, done
        self.verdict.submitEvidence(self.kevin, 7)
        self.assertEqual(self.verdict.score, 7)
        self.assertEqual(self.verdict.is_valid, True)
        self.assertEqual(self.verdict.is_done, True)

    def test_scribble_id(self):
        es = He.models.ExamScribble.objects.create(exam=self.exam)
        ps1 = He.models.ProblemScribble.objects.create(examscribble = es,\
                verdict = self.verdict)
        self.assertEqual(self.verdict.mathlete, None)

        try:
            es.assignTeam(self.team) # should fail
        except ValidationError:
            pass
        else:
            self.fail("System allowed assigning team to individual test")

        es.assignMathlete(self.mathlete) # This is better
        self.assertEqual(es.mathlete, self.mathlete)
        self.verdict.refresh_from_db()
        self.assertEqual(self.verdict.mathlete.id, self.mathlete.id)

# vim: fdm=indent foldnestmax=2 foldlevel=1
