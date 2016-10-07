from django.core.management.base import BaseCommand, CommandError
import helium as He
import itertools

class Command(BaseCommand):
    help = "For every verdict, runs updateDecisions on it"

    def handle(self, *args, **kwargs):
        # Naive version
#        for verdict in He.models.Verdict.objects.all():
#            verdict.updateDecisions()

        all_evidence = list(He.models.Evidence.objects.all())
        all_evidence.sort(key = lambda e : e.verdict.id)
        for verdict, evidences in itertools.groupby(all_evidence,
                key = lambda e : e.verdict):
            verdict.updateDecisions(list(evidences))
        # TODO write tests for this

