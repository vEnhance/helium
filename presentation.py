# Taken from babbage

from StringIO import StringIO
from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P

import helium as He

# Babbage
def get_odf_spreadsheet(sheets):
	doc = OpenDocumentSpreadsheet()
	spreadsheet = doc.spreadsheet
	for sheet_name, target_cells in sheets.iteritems():
		sheet = Table()
		spreadsheet.addElement(sheet)
		sheet.setAttribute("name", sheet_name)
		for target_row in target_cells:
			row = TableRow()
			for target_cell in target_row:
				cell = TableCell()
				cell.addElement(P(text=target_cell))
				row.addElement(cell)
			sheet.addElement(row)
	st = StringIO()
	doc.write(st)
	return st.getvalue()

# PRINTING OF RESULTS
def get_heading(s):
	return s.upper() + "\n" + "=" * 60 + "\n"
class NameResultRow:
	rank = None # assigned by parent ExamPrinter
	def __init__(self, row_name, scores):
		self.row_name = row_name
		self.scores = scores
		self.total = sum(scores)
class ResultPrinter:
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
				sheetrow += [round(s, ndigits = precision) if s else '0' for s in result.scores]
			sheet.append(sheetrow)
		return sheet

def RP_alphas(mathletes):
	results = [NameResultRow(row_name = unicode(mathlete),
				scores = [He.models.get_alpha(mathlete)])
				for mathlete in mathletes]
	return ResultPrinter(results)
def RP_exam(exam, entities):
	results = [NameResultRow(
			row_name = unicode(entity),
			scores = He.models.get_exam_scores(exam, entity)) \
			for entity in entities]
	return ResultPrinter(results)
def RP_alpha_sums(mathletes, teams):
	results = []
	for team in teams:
		scores = [He.models.get_alpha(m) for m in mathletes if m.team == team]
		scores.sort(reverse=True)
		results.append(NameResultRow(row_name = unicode(team), scores = scores))
	return ResultPrinter(results)

