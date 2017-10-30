from django.core.management.base import BaseCommand, CommandError
import helium as He

class Command(BaseCommand):
	help = "Deletes all Helium objects. Use before the tournament starts."

	def handle(self, *args, **kwargs):
		print "** WARNING: You are about to rinse the Helium database."
		print "This will CLEAR ALL DATA stored in the Helium application."
		print "Before this, it's recommended you save a copy of the data by running"
		print "python manage.py dumpdata helium --indent 1"

		if raw_input("   Type `y` to continue: ").strip() != 'y':
			return

		if raw_input("   Type `y` to also clear entities: ").strip() == 'y':
			He.models.Entity.objects.all().delete()
		# Cascading will delete all other relevant objects
		He.models.Exam.objects.all().delete()
		He.models.ThreadTaskRecord.objects.all().delete()
		He.models.GutsScoreFunc.objects.all().delete()
