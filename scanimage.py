"""
HELIUM
(c) 2016 Evan Chen
See LICENSE.txt for details.

scanimage.py

The main public method of this class is
get_answer_sheets( ... )

It takes in a file object (presumably from Django)
and then returns a generator which produces AnswerSheetImage objects.
The latter object is a class with several wrapper functions
which extract the relevant parts:
	AnswerSheetImage.get_full_file()
	AnswerSheetImage.get_name_file()
	AnswerSheetImage.get_problem_files() which is itself a generator
The return types of the cut-outs are Django InMemoryUploadedFile objects;
these allow storage in the database.

Dependencies:
	* The Wand Python module should be installed.
	* The system should have imagemagick, ghostscript, freetype
	  so that Wand can function.

On a system one can perform a "test run" by calling this as main
(and indeed static/answers/run-cutout-test.py symlinks to this file).
Simply call scanimage.py <filename.pdf>.
This will generate the cut-outs of the first page of that PDF file.
"""

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
CUTOUT_NAME_REGION = [0.00, 1.00, 0.07, 0.36] # name area
CUTOUT_PROBLEM_REGIONS = [
		[0.00, 0.55, 0.31, 0.49], # problem 1
		[0.00, 0.55, 0.42, 0.60], # problem 2
		[0.00, 0.55, 0.53, 0.71], # problem 3
		[0.00, 0.55, 0.60, 0.78], # problem 4
		[0.00, 0.55, 0.75, 0.93], # problem 5
		[0.45, 1.00, 0.31, 0.49], # problem 6
		[0.45, 1.00, 0.42, 0.60], # problem 7
		[0.45, 1.00, 0.53, 0.71], # problem 8
		[0.45, 1.00, 0.60, 0.78], # problem 9
		[0.45, 1.00, 0.75, 0.93], # problem 10
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
		self.full_image = Image(image = image)
		self.full_image.format = 'jpg' # convert to jpg
		self.image = Image(image = self.full_image)
		evaluate(self.image, 'threshold', 0.90)

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
		return to_django_file(self.full_image, filename)

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

if __name__ == "__main__":
	# This is for testing.
	# You call python scan.py <filename>
	# and it will output (in current directory) all image files

	import sys
	def saveDjangoFile(f):
		with open(f.name, 'w') as target:
			for chunk in f.chunks():
				target.write(chunk)

	if len(sys.argv) == 0:
		print "Need to specify a filename"
	else:
		filename = sys.argv[1]
		with open(filename) as pdf:
			sheets = get_answer_sheets(pdf)
			a = next(sheets) # answer sheet 1 only

			saveDjangoFile(a.get_full_file())
			saveDjangoFile(a.get_name_file())
			for pf in a.get_problem_files():
				saveDjangoFile(pf)
