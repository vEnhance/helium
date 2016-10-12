from django.core.management.base import BaseCommand, CommandError

import helium as He
import helium.algorithmic as algorithmic # brain for algorithmic scoring

class Command(BaseCommand):
	help = "Runs algorithmic scoring, and computes (then stores) all betas and alphas"

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

		# Run the main procedure, get alpha and beta values
		alphas, betas = algorithmic.main(problems, mathletes, scores)

		for mathlete_id, alpha in alphas.iteritems():
			a, _ = He.models.EntityAlpha.objects\
					.get_or_create(entity = He.models.Entity.objects.get(id=mathlete_id))
			a.cached_alpha = alpha
			a.save()

		for problem_id, beta in betas.iteritems():
			problem = He.models.Problem.objects.get(id = problem_id)
			problem.weight = beta
			problem.save()
