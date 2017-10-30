from django.core.management.base import BaseCommand, CommandError
import helium as He

class Command(BaseCommand):
	help = "Resets all grading data but does not delete entities or scans. "
	"This lets you restart the grading without redoing scanning."

	def handle(self, *args, **kwargs):
		print "Before this doing, it's recommended you save a copy of the data by running"
		print "python manage.py dumpdata helium --indent 1"

		if raw_input("   Type `dry` to continue: ").strip() != 'dry':
			return

		# Cascading will delete all other relevant objects
		He.models.Verdict.objects.filter(problem__exam__is_scanned=True)\
				.update(entity=None, score=None, is_valid=True, is_done=False)
		He.models.Verdict.objects.filter(problem__exam__is_scanned=False).delete()
		He.models.ExamScribble.objects.update(entity=None, last_sent_time=None)
		He.models.Evidence.objects.all().delete()
		He.models.EntityAlpha.objects.all().delete()
		He.models.ScoreRow.objects.all().delete()
