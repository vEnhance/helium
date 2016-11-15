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
			row, _ = He.models.ScoreRow.objects.get_or_create(
					category = category,
					entity = entity)
			row.set_scores(d[entity])
			row.save()
			all_rows.append(row)
		all_rows.sort(key = lambda row : -row.total)
		r = 0
		for n, row in enumerate(all_rows):
			if n == 0: r = 1
			elif all_rows[n-1].total != row.total: r = n+1
			row.rank = r
			row.save()

	def get_sweeps_scores(self, teams, scores, weight = 400):
		"""Given teams and scores, yield pairs (team, weighted_score)"""
		max_score = max(sum(sc) for sc in scores.values())\
				if len(scores) > 0 else 0
		if max_score > 0:
			mult = weight / max_score
		else:
			mult = 0
		for team in teams:
			yield (team, sum(scores[team]) * mult)

	def handle(self, *args, **kwargs):
		mathletes = list(He.models.Entity.mathletes.all())
		teams = list(He.models.Entity.teams.all())
		exams = list(He.models.Exam.objects.all())

		all_scores = {} # exam -> entity -> list of scores
		team_exam_scores = collections.defaultdict(list) # entity.id -> list of exam total scores

		# Scoring in usual way . . .
		for exam in exams:
			all_scores[exam] = collections.defaultdict(list)

		for verdict in He.models.Verdict.objects\
				.filter(score__isnull=False, entity__isnull=False)\
				.order_by('problem__problem_number'):
			exam = verdict.problem.exam
			entity = verdict.entity
			weighted_score = verdict.problem.weight * verdict.score \
					if verdict.problem.allow_partial else verdict.score
			all_scores[exam][entity].append(weighted_score)

		for exam in exams:
			entities = mathletes if exam.is_indiv else teams
			self.rank_entities(exam.name, entities, all_scores[exam])

			# HMMT-specific: sweepstake weights
			if not exam.is_indiv: # team exam
				set_of_scores = [sum(scores) for scores in all_scores[exam].values()]
				if len(set_of_scores) > 0 and max(set_of_scores) > 0:
					this_exam_weight = 400.0 / max(set_of_scores)
				else:
					this_exam_weight = 0
				for team in teams:
					team_exam_scores[team] = this_exam_weight * sum(all_scores[exam][team])

		# Individual alphas for all mathletes
		alphas = collections.defaultdict(lambda: (0.0,)) # mathlete -> (alpha,)
		for ea in He.models.EntityAlpha.objects.all(): # gdi
			alphas[ea.entity] = (ea.cached_alpha,)
		self.rank_entities("Individual Overall", mathletes, alphas)

		# Team Individual Aggregate
		aggr = collections.defaultdict(tuple)
		for team in teams:
			aggr[team] = (alphas[m][0] for m in mathletes if m.team == team)
		self.rank_entities("Team Aggregate", teams, aggr)

		sweeps = collections.defaultdict(list)
		# Each team event is worth 400 points:
		for exam in exams:
			if exam.is_indiv: continue
			for team, score in self.get_sweeps_scores(teams, all_scores[exam], weight = 400):
				sweeps[team].append(score)
		# Individual aggregate is worth 400 points:
		for team, score in self.get_sweeps_scores(teams, aggr, weight = 800):
			sweeps[team].append(score)
		self.rank_entities("Sweepstakes", teams, sweeps)
