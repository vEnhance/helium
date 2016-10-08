from django.core.management.base import BaseCommand, CommandError
import helium as He
import itertools
import logging

class Command(BaseCommand):
    help = "For every ExamScribble, runs updateScribbles on it if possible"

    def handle(self, *args, **kwargs):
        examscribbles = He.models.ExamScribble.objects\
                .all().prefetch_related('problemscribble_set')
        for es in examscribbles:
            es.updateScribbles(es.problemscribble_set.all())

# vim: expandtab
