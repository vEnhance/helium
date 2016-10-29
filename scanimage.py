from wand.image import Image
import wand.api
import wand.image
import ctypes
# This also requires: imagemagick, ghostscript, freetype

import StringIO
from django.core.files.uploadedfile import InMemoryUploadedFile

import time

# http://stackoverflow.com/a/26252400/4826845
# This is some hocus pocus to let us to threshold on the image
MagickEvaluateImage = wand.api.library.MagickEvaluateImage
MagickEvaluateImage.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_double]
def evaluate(self, operation, argument):
	MagickEvaluateImage(
		self.wand,
		wand.image.EVALUATE_OPS.index(operation),
		  self.quantum_range * float(argument))


# These are in (x1, x2, y1, y2) format
CUTOUT_FULL_REGION = [0.00, 1.00, 0.00, 1.00] # name area
CUTOUT_NAME_REGION = [0.00, 1.00, 0.07, 0.34] # name area
CUTOUT_PROBLEM_REGIONS = [
		[0.00, 0.55, 0.30, 0.45], # problem 1
		[0.00, 0.55, 0.42, 0.57], # problem 2
		[0.00, 0.55, 0.54, 0.69], # problem 3
		[0.00, 0.55, 0.65, 0.80], # problem 4
		[0.00, 0.55, 0.77, 0.92], # problem 5
		[0.45, 1.00, 0.30, 0.45], # problem 6
		[0.45, 1.00, 0.42, 0.57], # problem 7
		[0.45, 1.00, 0.54, 0.69], # problem 8
		[0.45, 1.00, 0.65, 0.80], # problem 9
		[0.45, 1.00, 0.77, 0.92], # problem 10
	]
def to_django_file(image, filename):
	"""http://stackoverflow.com/a/4544525/4826845
	This takes as input an image and a filename and as output
	returns an object which can be stored in Django file models"""

	io = StringIO.StringIO()
	image.save(io)
	f = InMemoryUploadedFile(io, None, filename, 'image/jpeg', io.len, None)
	return f
		
class AnswerSheetImage:
	"""This is a wrapper class that has all the data of a single answer sheet"""
	def __init__(self, image, fprefix):
		self.fprefix = fprefix
		self.image = Image(image = image)
		evaluate(self.image, 'threshold', 0.90)
		self.image.format = 'jpg' # convert to jpg


	def get_django_cutout(self, rect, filename):
		width = self.image.width
		height = self.image.height
		x1, x2, y1, y2 = rect
		left = int(width * x1)
		right = int(width * x2)
		top = int(height * y1)
		bottom = int(height * y2)
		with self.image[left:right, top:bottom] as cutout:
			return to_django_file(cutout, filename)

	def get_full_file(self):
		filename = '%s-full.jpg' % self.fprefix
		return self.get_django_cutout(CUTOUT_FULL_REGION, filename)

	def get_name_file(self):
		filename = '%s-name.jpg' % self.fprefix
		return self.get_django_cutout(CUTOUT_NAME_REGION, filename)

	def get_problem_files(self):
		for i, rect in enumerate(CUTOUT_PROBLEM_REGIONS):
			filename = '%s-prob-%02d.jpg' % (self.fprefix, i+1)
			yield self.get_django_cutout(rect, filename)

def get_answer_sheets(f, prefix = None):
	"""Given a file object f, yield answer sheet objects.
	The prefix, if specified, is appended to the start of filename."""
	curr_time = time.strftime("%Y%m%d-%H%M%S")
	if prefix is None:
		prefix = curr_time
	else:
		prefix = prefix + '-' + curr_time

	with Image(file = f, resolution = (140, 140)) as full_pdf:
		for i, page in enumerate(full_pdf.sequence):
			yield AnswerSheetImage(image = page,
					fprefix = "%s-sheet%04d" %(prefix, i+1))
