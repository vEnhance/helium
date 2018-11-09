from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import collections

from math import exp, log, floor

import helium as He

class Command(BaseCommand):
	help = "Runs algorithmic scoring according to new algorithm, weighting all the individual problems."

	def handle(self, *args, **kwargs):
		problems = He.models.Problem.objects.filter(exam__is_alg_scoring=True)
		problem_ids = problems.values_list('id', flat=True)

		verdicts = He.models.Verdict.objects\
				.filter(score__isnull=False, entity__isnull = False)\
				.filter(problem__exam__is_alg_scoring = True)\
				.values('problem__id', 'entity__id', 'score')
				# hence ordered triples (pid, entity id, score \in \{0,1\})
		num_solves = collections.defaultdict(int)
					# problem ids -> number of solves
		for v in verdicts:
			if v['score']:
				num_solves[v['problem__id']] += 1

		@transaction.atomic
		def update_scores(queryset):
			for problem in queryset:
				n = problem.problem_number
				N = num_solves[problem.id]
				if N == 0:
					w = 9.99
				else:
					w = exp(n/20.0) + max(8 - floor(log(N)), 2)
				problem.weight = w
				problem.save()
		update_scores(problems)
