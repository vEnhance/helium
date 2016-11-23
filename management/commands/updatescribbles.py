from django.core.management.base import BaseCommand, CommandError
import helium as He
import itertools
import logging

from django.db.models import F

class Command(BaseCommand):
	help = "For every ExamScribble, runs updateScribbles on it if possible"

	def handle(self, *args, **kwargs):
		queryset = He.models.Verdict.objects.filter(problemscribble__isnull=False)\

		queryset1 = queryset\
				.filter(entity__isnull=True)\
				.filter(problemscribble__examscribble__entity__isnull=False)
		queryset2 = queryset\
				.filter(entity__isnull=False)\
				.filter(problemscribble__examscribble__entity__isnull=True)
		queryset3 = queryset\
				.filter(entity__isnull=False)\
				.exclude(problemscribble__examscribble__entity = F("entity"))

		n = 0
		for v in itertools.chain(queryset1, queryset2, queryset3):
			v.entity = v.problemscribble.examscribble.entity
			v.save()
			n += 1
		return "%d updates" %n
