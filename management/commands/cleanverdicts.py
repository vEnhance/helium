from django.core.management.base import BaseCommand, CommandError
import helium as He
import itertools
import logging

from django.db.models import F

class Command(BaseCommand):
	help = "Delete unreachable verdicts: those with no exam scribble or entity"

	def handle(self, *args, **kwargs):
		queryset = He.models.Verdict.objects.filter(
				entity__isnull = True,
				problemscribble__isnull = True)
		n = queryset.count()
		queryset.delete()
		return "%d bad verdicts deleted" %n
