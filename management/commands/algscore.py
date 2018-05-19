from django.core.management.base import BaseCommand, CommandError

from math import exp, log, floor

import helium as He
import helium.algorithmic as algorithmic # brain for algorithmic scoring

class Command(BaseCommand):
	# help = "Runs algorithmic scoring, and computes (then stores) all betas and alphas"
	help = "Runs algorithmic scoring according to new algorithm and calculates new problem weights"

	def handle(self, *args, **kwargs):
		problems = [p.id for p in He.models.Problem.objects\
				.filter(exam__is_alg_scoring=True)]
		verdicts = He.models.Verdict.objects.filter(\
				problem__exam__is_alg_scoring = True)
		scores = [(v.problem.id, v.entity.id, v.score) for v in verdicts \
				if v.is_valid is True \
				and v.is_done is True \
				and v.entity is not None]
		mathletes = list(set([s[1] for s in scores]))

		solved_by = dict() # maps problem ids to sets of mathlete ids who solved that problem
		mathlete_totals = dict()
		for v in verdicts:
			if v.score:
				solved_by.setdefault(v.problem.id, set()).add(v.entity.id)

		assert len(problems) == len(solved_by)

		for p_id in solved_by:
			problem = He.models.Problem.objects.get(id=problem_id)
			n = problem.problem_number
			mathletes_who_solved = solved_by[p_id]
			N = len(mathletes_who_solved)
			w = exp(n/20) + max(8 - floor(log(N)), 2)
			problem.weight = w
			for m_id in mathletes_who_solved:
				if m_id not in mathlete_totals:
					mathlete_totals[m_id] = 0
				mathlete_totals[m_id] += w
			problem.save()

		for mathlete_id, alpha in mathlete_totals.iteritems():
			a, _ = He.models.EntityAlpha.objects\
					.get_or_create(entity = He.models.Entity.objects.get(id=mathlete_id))
			a.cached_alpha = alpha
			a.save()
