# This is taken from the old Babbage system
# The "math" portion of algorithmic scoring is here

# See https://www.hmmt.co/static/scoring-algorithm.pdf for English description

from math import exp, fabs
from operator import itemgetter

lowest_problem_weight = 3.0
highest_problem_weight = 8.0
threshold = 1e-4

def main(problems, mathletes, scores):
	assert len(problems) > 0
	assert len(mathletes) > 0

	problem_ids = problems
	mathlete_ids = mathletes
	
	alphas = {id : 0 for id in mathlete_ids}
	betas = {id : (lowest_problem_weight + highest_problem_weight) / 2 for id in problem_ids}

	math_took = {id : list() for id in mathlete_ids}
	math_solv = {id : list() for id in mathlete_ids}
	prob_took = {id : list() for id in problem_ids}
	prob_solv = {id : list() for id in problem_ids}
	
	for record in scores:
		problem, mathlete, result = record
		if not mathlete in math_took:
				continue
		math_took[mathlete].append(problem)
		prob_took[problem].append(mathlete)
		if result:
			math_solv[mathlete].append(problem)
			prob_solv[problem].append(mathlete)

	prev_alpha = dict([(id, 10000) for id in mathlete_ids])
	prev_beta = dict([(id, 0) for id in problem_ids])
	
	while norm(prev_alpha, alphas) > threshold or norm(prev_beta, betas) > threshold:
		prev_alpha = dict(alphas)
		prev_beta = dict(betas)
		
		for mathlete in prev_alpha.keys():
			alphas[mathlete] = binary_search_alpha(betas, math_took[mathlete], math_solv[mathlete])
		
		for problem in prev_beta.keys():
			betas[problem] = binary_search_beta(alphas, prob_took[problem], prob_solv[problem])
		
	return alphas, betas

def binary_search_alpha(betas, took, solved):
	low = 0.0
	high = 10000.0
	while (high - low > threshold):
		mid = (high + low) / 2
		if alpha_equation(mid, betas, took, solved) < 0:
			low = mid
		else:
			high = mid
	return (high + low) / 2
			
def binary_search_beta(alphas, took, solved):
	low = lowest_problem_weight
	high = highest_problem_weight
		
	while (high - low > threshold):
		mid = (high + low) / 2
		if beta_equation(mid, alphas, took, solved) > 0:
			low = mid
		else:
			high = mid
	return (high + low) / 2
			
def alpha_equation(alpha, betas, took, solved):
	result = 0
	
	result += alpha**2
	
	for id in took:
		beta = betas[id]
		result += beta * nu(alpha, beta) / (1 + nu(alpha, beta))

	for id in solved:
		beta = betas[id]
		result += -beta
		
	return result
	
def beta_equation(beta, alphas, took, solved):
	result = 0
	
	result += (beta - lowest_problem_weight) ** (-2) - (highest_problem_weight - beta) ** (-2)
	
	for id in took:
		alpha = alphas[id]
		result += 1 / alpha * nu(alpha, beta) / (1 + nu(alpha, beta))

	for id in solved:
		alpha = alphas[id]
		result += -1 / alpha
		
	return result
	
def nu(alpha, beta):
	return exp(-beta/alpha)
	
def norm(dict1, dict2):
	return max(map(fabs, [dict1[id] - dict2[id] for id in dict1.keys()]))
