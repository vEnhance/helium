from django.core.management.base import BaseCommand, CommandError
from registration.current import TEAMS, MATHLETES

import helium as He
import helium.algorithmic as algorithmic # brain for algorithmic scoring

class Command(BaseCommand):
    help = "Runs algorithmic scoring, and computes (then stores) all betas and alphas"

    def handle(self, *args, **kwargs):
        problems = [p.id for p in He.models.Problem.objects\
                .filter(exam__is_alg_scoring=True)]
        mathletes = [m.id for m in MATHLETES]
        
        verdicts = He.models.Verdict.objects.filter(\
                problem__exam__is_alg_scoring = True)
        scores = [(v.problem.id, v.mathlete.id, v.score) for v in verdicts \
                if v.is_valid is True \
                and v.is_done is True \
                and v.mathlete is not None]

        # Run the main procedure, get alpha and beta values
        alphas, betas = algorithmic.main(problems, mathletes, scores)

        for mathlete_id, alpha in alphas.iteritems():
            a, _ = He.models.MathleteAlpha.objects\
                    .get_or_create(mathlete__id = mathlete_id)
            a.cached_alpha = alpha
            a.save()

        for problem_id, beta in betas.iteritems():
            problem = He.models.Problem.objects.get(id = problem_id)
            problem.cached_beta = beta
            problem.save()

# vim: expandtab 
