from django.core.management.base import BaseCommand, CommandError
from registration.current import TEAMS, MATHLETES

import helium as He
import helium.algorithmic as algorithmic # brain for algorithmic scoring

class Command(BaseCommand):
    help = "Runs algorithmic scoring, and computes (then stores) all betas and alphas"

    def handle(self, *args, **kwargs):
        problems = He.models.Problem.objects.filter(exam__is_alg_scoring=True)
        mathletes = MATHLETES
        
        verdicts = He.models.Verdict.objects.filter(\
                problem__exam__is_alg_scoring = True)
        scores = [(v.mathlete, v.problem, v.score) for v in verdicts \
                if v.is_valid is True \
                and v.is_done is True \
                and v.mathlete is not None]
        print scores

        # Run the main procedure, get alpha and beta values
        alphas, betas = algorithmic.main(problems, mathletes, scores)

        for mathlete, alpha in alphas.iteritems():
            a = He.models.MathleteAlpha.get_or_create(mathlete = mathlete)
            a.cached_alpha = alpha
            a.save()

        for problem, beta in betas.iteritems():
            problem.cached_beta = beta
            problem.save()


# vim: expandtab 
