# Taken from babbage

from StringIO import StringIO
from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P

def get_spreadsheet(sheets):
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
