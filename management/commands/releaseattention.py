from django.core.management.base import BaseCommand, CommandError
import helium as He

class Command(BaseCommand):
	help = "Releases all examscribbles from attention"

	def handle(self, *args, **kwargs):
		examscribbles = He.models.ExamScribble.objects.exclude(needs_attention=u'')
		for es in examscribbles:
			es.needs_attention = ""
			es.save()
