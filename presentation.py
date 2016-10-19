"""
HELIUM
Evan Cheno, 2016

presentation.py

This is responsible for the final presentation of results of tournament.
It generates both text files and ODF spreadsheets.
The get_odf_spreadsheet is an improved version of one inside Babbage.
"""

from StringIO import StringIO
from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P

import helium as He

# Why isn't this built-in?
def valuetype(val):
	if isinstance(val, int): return 'float'
	elif isinstance(val, float): return 'float'
	elif isinstance(val, bool): return 'boolean'
	else: return 'string'

def get_odf_spreadsheet(sheets):
	"""Creates a spreadsheet from a dictionary sheets of 
	dictionary entries sheetname -> nested list of rows"""
	doc = OpenDocumentSpreadsheet()
	spreadsheet = doc.spreadsheet
	for sheet_name, list_rows in sheets.iteritems():
		sheet = Table()
		spreadsheet.addElement(sheet)
		sheet.setAttribute("name", sheet_name)
		for list_row in list_rows:
			table_row = TableRow()
			for cell_content in list_row:
				vtype = valuetype(cell_content)
				table_cell = TableCell(valuetype = vtype, value = cell_content)
				table_row.addElement(table_cell)
				if vtype == "string":
					table_cell.addElement(P(text=cell_content))
			sheet.addElement(table_row)
	st = StringIO()
	doc.write(st)
	return st.getvalue()

def get_heading(s):
	"""Creates a heading from a string s"""
	return s.upper() + "\n" + "=" * 60 + "\n"
class NameResultRow:
	"""This is a container object which hold the information of a *row*;
	this includes a name (e.g. mathlete or team name)
	and one or more scores, which are printed one at a time.
	The sum of the scores is also computed and stored as row.total"""
	rank = None # assigned by parent ExamPrinter
	def __init__(self, row_name, scores):
		self.row_name = row_name
		self.scores = scores
		self.total = sum(scores)
class ResultPrinter:
	"""This is a object which takes in several result rows,
	stored as self.results.
	It will assign ranks to these rows (e.g. 1st, 2nd, etc.).
	Then, the facilities RP.get_table and RP.get_rows
	will respectively create a text table and a list of Python lists
	(the latter which should probably be fed into get_odf_spreadsheet"""
	def __init__(self, results):
		results.sort(key = lambda r : -r.total)
		r = 0
		for n, result in enumerate(results):
			if n == 0: r = 1
			elif results[n-1].total != result.total: r = n+1
			result.rank = r
		self.results = results
	def get_table(self, heading = None, num_show = None, num_named = None,
			float_string = "%4.2f", int_string = "%4d"):
		output = get_heading(heading) if heading is not None else ''
		for result in self.results:
			if num_show is not None and result.rank > num_show:
				break
			output += "%4d. " % result.rank
			output += "%7.2f"  % result.total if type(result.total) == float \
					else "%7d" % result.total
			if len(result.scores) > 1: # sum of more than one thing
				output += "  |  "
				output += " ".join([float_string%x if type(x)==float else int_string%x \
						for x in result.scores])
			output += "  |  "
			if num_named is None or result.rank <= num_named:
				output += result.row_name
			output += "\n"
		output += "\n"
		return output
	def get_rows(self, precision = 2):
		sheet = [["Rank", "Name", "Total"]]
		for result in self.results:
			sheetrow = [result.rank, result.row_name, \
					round(result.total, ndigits = precision)]
			if len(result.scores) > 1:
				sheetrow += [round(s, ndigits = precision) if s else 0 for s in result.scores]
			sheet.append(sheetrow)
		return sheet


def RP_alphas(mathletes):
	"""Creates a ResultPrinter for a set of mathletes,
	by looking up their alpha values"""
	results = [NameResultRow(row_name = unicode(mathlete),
				scores = [He.models.get_alpha(mathlete)])
				for mathlete in mathletes]
	return ResultPrinter(results)
def RP_exam(exam, entities):
	"""Creates a ResultPrinter for a set of exams and entities,
	by looking up their scores for the exam"""
	results = [NameResultRow(
			row_name = unicode(entity),
			scores = He.models.get_exam_scores(exam, entity)) \
			for entity in entities]
	return ResultPrinter(results)
def RP_alpha_sums(mathletes, teams):
	"""Creates a ResultPrinter for a set of mathletes and teams
	by summing the alpha values of the mathletes"""
	results = []
	for team in teams:
		scores = [He.models.get_alpha(m) for m in mathletes if m.team == team]
		scores.sort(reverse=True)
		results.append(NameResultRow(row_name = unicode(team), scores = scores))
	return ResultPrinter(results)
