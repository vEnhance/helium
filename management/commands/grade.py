from django.core.management.base import BaseCommand, CommandError
import helium as He
import collections

class Command(BaseCommand):
	help = "Computes all scores, and stores them in database of ScoreRows"

	def rank_entities(self, category, entities, d):
		"""Stores ranks and such
		Input: entities is a list of entities
		d is a (default)dict of form entity -> score list"""
		all_rows = []
		for entity in entities:
			row = He.models.ScoreRow(category = category, entity = entity)
			row.set_scores(d[entity.id])
			all_rows.append(row)
		all_rows.sort(key = lambda row : -row.total)
		r = 0
		for n, row in enumerate(all_rows):
			if n == 0: r = 1
			elif all_rows[n-1].total != row.total: r = n+1
			row.rank = r
		return all_rows

	def get_sweeps_scores(self, teams, scores, weight = 400):
		"""Given teams and scores, yield pairs (team, weighted_score)"""
		def total(sc):
			return sum([x for x in sc if x is not None])
		max_score = max(total(sc) for sc in scores.values())\
				if len(scores) > 0 else 0
		if max_score > 0:
			mult = float(weight) / max_score
		else:
			mult = 0
		for team in teams:
			yield (team, total(scores[team.id]) * mult)

	def handle(self, *args, **kwargs):
		mathletes = list(He.models.Entity.mathletes.all())
		teams = list(He.models.Entity.teams.all())
		exams = list(He.models.Exam.objects.all())

		team_exam_scores = collections.defaultdict(list) # entity.id -> list of exam total scores
		all_rows = [] # all rows

		# Scoring in usual way . . .
		all_scores = {} # exam.id -> entity.id -> list of scores
		for exam in exams:
			all_scores[exam.id] = collections.defaultdict(list)

		exam_pcount = list(He.models.Problem.objects.all().values_list('exam__id', flat=True))
		for d in He.models.Verdict.objects\
				.filter(score__isnull=False, entity__isnull=False)\
				.values("problem__exam_id", "entity_id",
						"problem__weight", "score", "problem__allow_partial",
						"problem__problem_number"):
			prob_number = d['problem__problem_number']
			exam_id = d['problem__exam_id']
			entity_id = d['entity_id']
			weighted_score = d['problem__weight'] * d['score'] \
					if not d['problem__allow_partial'] else d['score']
			if not entity_id in all_scores[exam_id]:
				all_scores[exam_id][entity_id] = [None] * exam_pcount.count(exam_id)
			all_scores[exam_id][entity_id][prob_number-1] = weighted_score

		for exam in exams:
			entities = mathletes if exam.is_indiv else teams
			all_rows += self.rank_entities(exam.name, entities, all_scores[exam.id])

		# Individual alphas for all mathletes
		# For now this is duplication, but if we e.g. decide we ever
		# want to switch to using sums of scores on tests,
		# this way we can do so
		alphas = collections.defaultdict(lambda: (0.0,)) # mathlete -> (alpha,)
		for d in He.models.EntityAlpha.objects.values('entity_id', 'cached_alpha'):
			alphas[d['entity_id']] = (d['cached_alpha'],)
		all_rows += self.rank_entities("Individual Overall", mathletes, alphas)

		# Team Individual Aggregate
		aggr = collections.defaultdict(tuple)
		for team in teams:
			aggr[team.id] = [alphas[m.id][0] for m in mathletes if m.team == team]
			aggr[team.id].sort(reverse=True)
		all_rows += self.rank_entities("Team Aggregate", teams, aggr)

		sweeps = collections.defaultdict(list)
		# Each team event is worth 400 points:
		for exam in exams:
			if exam.is_indiv: continue
			for team, score in self.get_sweeps_scores(teams, all_scores[exam.id], weight = 400):
				sweeps[team.id].append(score)
		# Individual aggregate is worth 400 points:
		for team, score in self.get_sweeps_scores(teams, aggr, weight = 800):
			sweeps[team.id].append(score)
		all_rows += self.rank_entities("Sweepstakes", teams, sweeps)

		He.models.ScoreRow.objects.all().delete() # wipe old data
		He.models.ScoreRow.objects.bulk_create(all_rows)
