"""
HELIUM 2
(c) 2017 Evan Chen
See LICENSE.txt for details.

presentation.py

This is responsible for the final presentation of results of tournament.
It generates both text files and list of lists;
in the latter case, sheetapi.py has a function which makse them into spreadsheets.
"""

import itertools
import collections
import time
import re
import sheetapi

import helium as He

def get_heading(s):
	"""Creates a heading from a string s"""
	return s.upper() + "\n" + "=" * 60 + "\n"

def tex_escape(text):
	"""
		:param text: a plain text message
		:return: the message escaped to appear correctly in LaTeX
		https://stackoverflow.com/a/25875504/4826845
	"""
	conv = {
		'&': r'\&',
		'%': r'\%',
		'$': r'\$',
		'#': r'\#',
		'_': r'\_',
		'{': r'\{',
		'}': r'\}',
		'~': r'\textasciitilde{}',
		'^': r'\^{}',
		'\\': r'\textbackslash{}',
		'<': r'\textless ',
		'>': r'\textgreater ',
	}
	regex = re.compile('|'.join(re.escape(unicode(key)) for key in sorted(conv.keys(), key = lambda item: - len(item))))
	return regex.sub(lambda match: conv[match.group()], text)


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
			self.scores = [float(x) if x != 'None' else None \
					for x in d['cached_score_string'].split(',')] # so much for DRY, qq
		else:
			self.scores = []
		self.rank = d['rank']
		if d['entity__team__name']:
			self.name = "%s (%s)" % (d['entity__name'], d['entity__team__name'])
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
		if len(self.rows) > 0:
			self.len = max(len(r.scores) for r in self.rows)
		else:
			self.len = 0
		self.rows.sort(key = lambda r : r.rank)


	def get_table(self, heading = None, num_show = None,
			num_named = None, zero_pad = True,
			float_string = "%4.2f", int_string = "%4d"):
		output = get_heading(heading) if heading is not None else ''
		pre_num = heading[0] if heading else " "
		if len(self.rows) == 0: return output # assume >= 1 entry

		def score_to_string(x):
			"""Given x \in [Int, Float, None], return a string rep"""
			if x is None:
				if zero_pad:
					return int_string % 0
				else:
					return (int_string % 99).replace("9", "-")
					# use "--" for blanks:
					# it's better than "-" since it's more obvious
					# otherwise it's easy to overlook when sanity checking results
					# (cf. HMMT Feb 2018 >_<)
			elif type(x) == int or x == 0:
				return int_string % x
			elif type(x) == float:
				return float_string % x
			else:
				return str(x)

		# Take longest row for zero padding
		for row in self.rows:
			if num_show is not None and row.rank > num_show:
				break
			if zero_pad is True:
				scores = row.scores + [0,] * (self.len-len(row.scores))
			else:
				scores = row.scores
			output += pre_num + "%4d. " % row.rank
			output += "%7.2f"  % row.total
			output += "  |  "
			output += " ".join([score_to_string(x) for x in scores])
			output += "  |  "
			if num_named is None or row.rank <= num_named:
				output += row.name
			output += "\n"
		output += "\n"
		return output

	def get_frames(self, heading):
		def nth(n):
			return str(n) + {1:'st', 2:'nd', 3:'rd'}\
					.get(n if (n < 20) else (n % 10), 'th')
		desc_rows = sorted(self.rows, key = lambda r : -r.rank)
		output = r"\section{" + heading + "}" + "\n"
		for rank, group in itertools.groupby(desc_rows, key = lambda r : r.rank):
			title = heading
			output += r"\scoreframe{" + title + "}{%" + "\n"
			# First get names of students/teams
			for row in group:
				output += " " * 2 + r"\item[" + nth(row.rank) + "] " + tex_escape(row.name) + "\n"
			output += "}{"
			score = row.total # grab last score WLOG
			output += str(int(score)) if score.is_integer() else "%.3f" %score
			output += r"}" + "\n"
		output += r"\begin{frame}{" + heading + "}" + "\n"
		output += r"\begin{enumerate}" + "\n"
		for row in reversed(desc_rows):
			output += " "*4 + r"\item[" + nth(row.rank) + "] " + tex_escape(row.name) + "\n"
		output += r"\end{enumerate}" + "\n"
		output += r"\end{frame}" + "\n"
		output += r"% End awards for " + heading
		return output

	def get_sheet(self, precision = 4, heading = None):
		header_row = ["Rank", "Name", "Total"]
		if self.len > 1 and heading is not None:
			pre_num = heading[0] if heading else ""
			header_row += [pre_num + str(i) for i in range(1,self.len+1)]
		sheet = [header_row]
		for row in self.rows:
			sheetrow = [row.rank, row.name, \
					round(row.total, ndigits = precision)]
			if len(row.scores) > 1:
				sheetrow += [round(s, ndigits = precision) if s is not None\
						else None for s in row.scores]
			sheet.append(sheetrow)
		return sheet

RP = ResultPrinter # for brevity

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

HELIUM 2 (c) 2017 Evan Chen
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

	## Individual Results
	rows = all_rows['Individual Overall']
	output += RP(rows).get_table(heading = "Overall Individual Awards",
			num_show = num_show, num_named = num_named,
			float_string = "%5.2f", int_string = "%5d")
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
			num_show = num_show, num_named = num_named,
			float_string = "%6.2f", int_string = "%6d")
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

def HMMT_spreadsheet(queryset = None):
	sheets = collections.OrderedDict() # sheet name -> rows
	all_rows = get_score_rows(queryset)

	for exam in He.models.Exam.objects.all():
		sheets[unicode(exam)] = RP(all_rows[exam.name]).get_sheet(heading = exam.name)
	sheets["Indiv"] = RP(all_rows["Individual Overall"]).get_sheet(heading = None)
	sheets["Aggr"] = RP(all_rows["Team Aggregate"]).get_sheet(heading = "")
	sheets["Sweeps"] = RP(all_rows["Sweepstakes"]).get_sheet(heading = None)

	odf = sheetapi.get_odf_spreadsheet(sheets)
	return odf

## AWARDS

BEAMER_PREAMBLE = r"""\documentclass{beamer}
%% HMMT BEAMER AWARDS TEMPLATE
%% (c) 2017 Evan Chen as part of Helium
%% See LICENSE.txt for details.

\usetheme{CambridgeUS} % fitting

%% UNCOMMENT THIS once you have the image in your working directory
\setbeamertemplate{logo}{%
%\includegraphics[height=0.8cm]{logo-transparent-black.png}%
}

\setbeamertemplate{footline}{}%
\setbeamertemplate{headline}{
  \leavevmode%
  \hbox{%
  \begin{beamercolorbox}[wd=.5\paperwidth,ht=2.65ex,dp=1.5ex,right]{author in head/foot}%
    \usebeamerfont{author in head/foot}\insertshortauthor\hspace*{2ex}
  \end{beamercolorbox}%
  \begin{beamercolorbox}[wd=.5\paperwidth,ht=2.65ex,dp=1.5ex,left]{date in head/foot}%
  \usebeamerfont{date in head/foot}\hspace*{2ex}\tournament
  \end{beamercolorbox}}%
  \vskip0pt%
}

\newcommand{\scoreframe}[3]{%
\begin{frame}{#1}
\Large With a score of \alert{#3},
\begin{enumerate}
\setlength{\itemindent}{1.5em}
\Large #2
\end{enumerate}
\end{frame}%
}

\newcommand{\tournament}{\ifcase \month \or January\or February\or March\or %
April\or May \or June\or July\or August\or September\or October\or November\or %
December\fi\ \number \year}

\title{\tournament\ Awards}
\author{Harvard-MIT Math Tournament}
\date{\today}
\begin{document}
\maketitle

\section{Staff and Sponsors}
\begin{frame}
\Huge \alert{TODO}
\end{frame}
""".strip()

BEAMER_POSTAMBLE = r"""
\section{Closing}
\begin{frame}
\begin{center}
\huge \alert{\insertauthor \\ \tournament}
\end{center}
\begin{center}
\LARGE Thank you! See you next year!
\end{center}
\end{frame}
\end{document}"""


def HMMT_awards(queryset = None):
	"""Generates an awards ceremony beamer for rows in `queryset`"""
	output = BEAMER_PREAMBLE
	output += "\n" * 4

	all_rows = get_score_rows(queryset)
	RP = ResultPrinter # for brevity

	## Individual Exams
	indiv_exams = He.models.Exam.objects.filter(is_indiv=True)
	for exam in indiv_exams:
		rows = all_rows[exam.name]
		output += RP(rows).get_frames(heading = unicode(exam))
		output += "\n" * 2

	## Team Exams
	team_exams = He.models.Exam.objects.filter(is_indiv=False)
	for exam in team_exams:
		rows = all_rows[exam.name]
		output += RP(rows).get_frames(heading = unicode(exam))
		output += "\n" * 2

	## Top Individuals (Aggregate)
	rows = all_rows['Individual Overall']
	output += RP(rows).get_frames("Top Individuals") + "\n" * 2

	# Sweepstakes
	rows = all_rows['Sweepstakes']
	output += RP(rows).get_frames("Sweepstakes")
	output += "\n" * 2

	output += BEAMER_POSTAMBLE
	return output
