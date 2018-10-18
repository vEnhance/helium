"""
HELIUM 2
(c) 2017 Evan Chen
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

This requires GhostScript.

On a system one can perform a "test run" by calling this as main
(and indeed static/answers/run-cutout-test.py symlinks to this file).
Simply call scanimage.py <filename.pdf>.
This will generate the cut-outs of the first page of that PDF file.

By design, this module is agnostic to remaining components of helium.
"""

import ctypes
import ghostscript
import tempfile
import os
from PIL import Image

import StringIO
from django.core.files.uploadedfile import InMemoryUploadedFile

# These are in (x1, x2, y1, y2) format
CUTOUT_FULL_REGION = [0.00, 1.00, 0.00, 1.00] # full region
CUTOUT_NAME_REGION = [0.00, 1.00, 0.02, 0.36] # name area
CUTOUT_PROBLEM_REGIONS = [
		[0.00, 0.55, 0.31, 0.49], # problem 1
		[0.00, 0.55, 0.42, 0.60], # problem 2
		[0.00, 0.55, 0.52, 0.70], # problem 3
		[0.00, 0.55, 0.62, 0.80], # problem 4
		[0.00, 0.55, 0.74, 0.92], # problem 5
		[0.45, 1.00, 0.31, 0.49], # problem 6
		[0.45, 1.00, 0.42, 0.60], # problem 7
		[0.45, 1.00, 0.52, 0.70], # problem 8
		[0.45, 1.00, 0.62, 0.80], # problem 9
		[0.45, 1.00, 0.74, 0.92], # problem 10
	]
PROBLEMS_PER_SHEET = 10

def to_django_file(image, filename):
	"""http://stackoverflow.com/a/4544525/4826845
	This takes as input an image and a filename and as output
	returns an object which can be stored in Django file models"""

	io = StringIO.StringIO()
	image.save(io, format='JPEG')
	f = InMemoryUploadedFile(io, None, filename, 'image/jpeg', io.len, None)
	return f

class AnswerSheetImage:
	"""This is a wrapper class that has all the data of a single answer sheet"""
	def __init__(self, image, name):
		self.full_image = image
		self.name = name

	def get_django_cutout(self, rect, filename):
		width = self.full_image.width
		height = self.full_image.height
		x1, x2, y1, y2 = rect
		left = int(width * x1)
		right = int(width * x2)
		top = int(height * y1)
		bottom = int(height * y2)
		crop = self.full_image.crop((left, top, right, bottom))
		return to_django_file(crop, filename)

	def get_full_file(self):
		filename = '%s-full.jpg' % self.name
		return to_django_file(self.full_image, filename)

	def get_name_file(self):
		filename = '%s-name.jpg' % self.name
		return self.get_django_cutout(CUTOUT_NAME_REGION, filename)

	def get_problem_files(self):
		for i, rect in enumerate(CUTOUT_PROBLEM_REGIONS):
			filename = '%s-prob-%02d.jpg' % (self.name, i+1)
			yield self.get_django_cutout(rect, filename)

def get_answer_sheets(in_memory_fh, filename):
	"""Given a file object f, yield answer sheet objects."""
	if filename.endswith('.pdf'): # which SHOULD be the case!
		prefix = filename[:-4] # strip pdf extension
		tempdir = tempfile.mkdtemp(prefix='tmp-helium-')

		# from https://stackoverflow.com/a/36113000/4826845
		with tempfile.NamedTemporaryFile(prefix='scan-helium-',
				delete=False, suffix=".pdf") as temp_pdf_file:
			temp_pdf_file.write(in_memory_fh.read())
		pdf_input_path = temp_pdf_file.name
		args = ["evan chen is really cool", # actual value doesn't matter
				"-dNOPAUSE",
				"-sDEVICE=jpeg",
				"-r144",
				"-sOutputFile=" + os.path.join(tempdir, prefix+"-sheet%04d.jpg"),
				pdf_input_path]
		ghostscript.Ghostscript(*args)

		for n in xrange(1,10000):
			name = prefix+"-sheet%04d" % n
			image_path = os.path.join(tempdir, name+".jpg")
			if not os.path.exists(image_path):
				break
			yield AnswerSheetImage(image = Image.open(image_path), name = name)

	elif filename.endswith('.zip'):
		prefix = filename[:-4] # strip zip extension
		raise NotImplementedError("Not yet implemented zip")

	else:
		raise NotImplementedError("You are a terrible person")

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
		sys.stderr.write("Need to specify a filename" + "\n")
	else:
		filename = sys.argv[1]
		with open(filename) as pdf:
			sheets = get_answer_sheets(pdf, "example.pdf")
			a = next(sheets) # answer sheet 1 only

			saveDjangoFile(a.get_full_file())
			saveDjangoFile(a.get_name_file())
			for pf in a.get_problem_files():
				saveDjangoFile(pf)
