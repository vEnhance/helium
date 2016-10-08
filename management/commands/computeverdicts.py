from django.core.management.base import BaseCommand, CommandError
import helium as He
import itertools

class Command(BaseCommand):
    help = "For every verdict, runs updateDecisions on it"

    def handle(self, *args, **kwargs):
		verdicts = He.models.Verdict.objects.all().prefetch_related('evidence_set')
		for verdict in verdicts:
			verdict.updateDecisions(verdict.evidence_set.all())
