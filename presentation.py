"""
HELIUM
(c) 2016 Evan Chen
See LICENSE.txt for details.

presentation.py

This is responsible for the final presentation of results of tournament.
It generates both text files and ODF spreadsheets.
The get_odf_spreadsheet is an improved version of one inside Babbage.
"""

from StringIO import StringIO
from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P

import itertools
import collections
import time

import helium as He

# Why isn't this built-in?
def valuetype(val):
	if isinstance(val, bool): return 'boolean'
	elif isinstance(val, int): return 'float' # somehow isinstance(True, int) = True !?
	elif isinstance(val, float): return 'float'
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
				if vtype == "boolean":
					cell_content = ("YES" if cell_content else "NO")
					vtype = "string"
				table_cell = TableCell(valuetype=vtype, value=cell_content)
				if vtype == "string":
					table_cell.addElement(P(text=str(cell_content)))
				table_row.addElement(table_cell)
			sheet.addElement(table_row)
	st = StringIO()
	doc.write(st)
	return st.getvalue()

def get_heading(s):
	"""Creates a heading from a string s"""
	return s.upper() + "\n" + "=" * 60 + "\n"


def get_score_rows(queryset = None):
	if queryset is None:
		queryset = He.models.ScoreRow.objects.all()
	dicts = queryset.values(
			'category', 'entity__name', 'rank', 'total', 'cached_score_string',
			'entity__is_team', 'entity__shortname', 'entity__team__name')
	ret = collections.defaultdict(list)
	for d in dicts:
		ret[d['category']].append(ResultRow(d))
	return ret

class ResultRow:
	"""Container object"""
	def __init__(self, d):
		"""Input: a dictionary d from ScoreRow.object.values()"""
		self.total = d['total']
		if len(d['cached_score_string']) > 0:
			self.scores = [float(x) for x in d['cached_score_string'].split(',')] # so much for DRY
		else:
			self.scores = []
		self.rank = d['rank']
		if d['entity__team__name']:
			self.name = "%s [%s]" % (d['entity__name'], d['entity__team__name'])
		else:
			self.name = d['entity__name']

class ResultPrinter:
	"""This is a object which takes in several ScoreRow objects,
	stored as self.results.
	The facilities RP.get_table and RP.get_rows
	will respectively create a text table and a list of Python lists
	(the latter which should probably be fed into get_odf_spreadsheet"""
	def __init__(self, rows):
		self.rows = list(rows)
		self.rows.sort(key = lambda r : r.rank)
	def get_table(self, heading = None, num_show = None, num_named = None, zero_pad = True,
			float_string = "%4.2f", int_string = "%4d"):
		output = get_heading(heading) if heading is not None else ''
		if len(self.rows) == 0: return output # assume >= 1 entry
		max_length = max(len(r.scores) for r in self.rows) # take longest row for zero padding
		for row in self.rows:
			if num_show is not None and row.rank > num_show:
				break
			output += "%4d. " % row.rank
			output += "%7.2f"  % row.total
			if max_length > 1: # sum of more than one thing
				if zero_pad:
					scores = row.scores + [0,] * (max_length - len(row.scores))
				else:
					scores = row.scores
				output += "  |  "
				output += " ".join([int_string %x if type(x) == int or x == 0 \
						else float_string %x  for x in scores])
			output += "  |  "
			if num_named is None or row.rank <= num_named:
				output += row.name
			output += "\n"
		output += "\n"
		return output

	def get_sheet(self, precision = 2):
		sheet = [["Rank", "Name", "Total"]]
		for row in self.rows:
			sheetrow = [row.rank, row.name, \
					round(row.total, ndigits = precision)]
			if len(row.scores) > 1:
				sheetrow += [round(s, ndigits = precision) if s else 0 for s in row.scores]
			sheet.append(sheetrow)
		return sheet


### HMMT TEXT REPORT

INIT_TEXT_BANNER = """
 .----------------.  .----------------.  .----------------.  .----------------. 
| .--------------. || .--------------. || .--------------. || .--------------. |
| |  ____  ____  | || | ____    ____ | || | ____    ____ | || |  _________   | |
| | |_   ||   _| | || ||_   \  /   _|| || ||_   \  /   _|| || | |  _   _  |  | |
| |   | |__| |   | || |  |   \/   |  | || |  |   \/   |  | || | |_/ | | \_|  | |
| |   |  __  |   | || |  | |\  /| |  | || |  | |\  /| |  | || |     | |      | |
| |  _| |  | |_  | || | _| |_\/_| |_ | || | _| |_\/_| |_ | || |    _| |_     | |
| | |____||____| | || ||_____||_____|| || ||_____||_____|| || |   |_____|    | |
| |              | || |              | || |              | || |              | |
| '--------------' || '--------------' || '--------------' || '--------------' |
 '----------------'  '----------------'  '----------------'  '----------------' 

See <a href="https://www.hmmt.co/static/scoring-algorithm.pdf">https://www.hmmt.co/static/scoring-algorithm.pdf</a> for a description
of the scoring algorithm used on the individual tests.
 """.strip()

FINAL_TEXT_BANNER = """
 ('-. .-.   ('-.                               _   .-')    
( OO )  / _(  OO)                             ( '.( OO )_  
,--. ,--.(,------.,--.      ,-.-') ,--. ,--.   ,--.   ,--.)
|  | |  | |  .---'|  |.-')  |  |OO)|  | |  |   |   `.'   | 
|   .|  | |  |    |  | OO ) |  |  \|  | | .-') |         | 
|       |(|  '--. |  |`-' | |  |(_/|  |_|( OO )|  |'.'|  | 
|  .-.  | |  .--'(|  '---.',|  |_.'|  | | `-' /|  |   |  | 
|  | |  | |  `---.|      |(_|  |  ('  '-'(_.-' |  |   |  | 
`--' `--' `------'`------'  `--'    `-----'    `--'   `--' 

HELIUM (c) 2016 Evan Chen
""".strip()

def HMMT_text_report(queryset = None,
		num_show = None, num_named = None, zero_pad = True):
	"""Explanation of potions:
	num_show: Display only the top N entities
	num_named: Suppress the names of entities after rank N
	zero_pad: Whether missing scores should be zero-padded
	The other booleans are self explanatory."""

	output = '<!DOCTYPE html>' + "\n"
	output += '<html><head></head><body>' + "\n"
	output += '<pre style="font-family:Consolas,Monaco,Lucida Console,Liberation Mono,'\
			'DejaVu Sans Mono,Bitstream Vera Sans Mono,Courier New, monospace;">' + "\n"
	output += INIT_TEXT_BANNER + "\n\n"

	all_rows = get_score_rows(queryset)

	RP = ResultPrinter # for brevity

	## Individual Results
	rows = all_rows['Individual Overall']
	output += RP(rows).get_table("Overall Individuals (Alphas)",
			num_show = num_show, num_named = num_named)
	output += "\n"

	indiv_exams = He.models.Exam.objects.filter(is_indiv=True)
	for exam in indiv_exams:
		rows = all_rows[exam.name]
		output += RP(rows).get_table(heading = unicode(exam),
				num_show = num_show, num_named = num_named, zero_pad = zero_pad)
	output += "\n"

	## Team Results
	team_exams = He.models.Exam.objects.filter(is_indiv=False)
	for exam in team_exams:
		rows = all_rows[exam.name]
		output += RP(rows).get_table(heading = unicode(exam),
				num_show = num_show, num_named = num_named, zero_pad = zero_pad,
				float_string = "%2.0f", int_string = "%2d")
		output += "\n"

	# Indiv aggregate
	rows = all_rows["Team Aggregate"]
	output += RP(rows).get_table("Team Aggregate",
			num_show = num_show, num_named = num_named)
	output += "\n"

	# Sweepstakes
	rows = all_rows["Sweepstakes"]
	output += RP(rows).get_table("Sweepstakes",
			num_show = num_show, num_named = None,
			float_string = "%7.2f", int_string = "%7d")
	output += "\n"

	output += "This report was generated by Helium at " + time.strftime('%c') + "."
	output += "\n\n"
	output += FINAL_TEXT_BANNER + "\n"
	output += "</pre></body></html>"
	return output

