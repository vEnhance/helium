from django.core.management.base import BaseCommand, CommandError
import helium as He

class Command(BaseCommand):
	help = "Releases all examscribbles from attention"

	def handle(self, *args, **kwargs):
		examscribbles = He.models.ExamScribble.objects.filter(needs_attention=True)
		for es in examscribbles:
			es.needs_attention = False
			es.save()
