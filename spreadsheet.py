"""
HELIUM 2
(c) 2017 Evan Chen
See LICENSE.txt for details.

presentation.py

This produces spreadsheets in ODF format from Python lists.
The get_odf_spreadsheet is an improved version of one inside Babbage.
"""

from StringIO import StringIO
from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P

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
