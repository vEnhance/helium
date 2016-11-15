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

import helium as He
import itertools

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
				output += unicode(row.entity)
			output += "\n"
		output += "\n"
		return output

	def get_sheet(self, precision = 2):
		sheet = [["Rank", "Name", "Total"]]
		for row in self.rows:
			sheetrow = [row.rank, unicode(row.entity), \
					round(row.total, ndigits = precision)]
			if len(row.scores) > 1:
				sheetrow += [round(s, ndigits = precision) if s else 0 for s in row.scores]
			sheet.append(sheetrow)
		return sheet
