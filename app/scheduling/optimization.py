import numpy as np

def calculate_fitness(schedule, assignments):
    coverage_score = calculate_coverage_score(schedule, assignments)
    cost_score = calculate_cost_score(schedule, assignments)
    preference_score = calculate_preference_score(assignments)
    fairness_score = calculate_fairness_score(assignments)
    
    return coverage_score + cost_score + preference_score + fairness_score

def calculate_coverage_score(schedule, assignments):
    # Implement logic to calculate how well the schedule meets demand requirements
    pass

def calculate_cost_score(schedule, assignments):
    # Implement logic to calculate the cost of the workforce mix
    pass

def calculate_preference_score(assignments):
    score = 0
    for assignment in assignments:
        employee = assignment.shift.employee
        # Shift preference
        shift_index = (assignment.shift.start_time.hour - 6) // 8
        shift_preference = employee.shift_preferences.index(shift_index + 1) + 1
        score += (4 - shift_preference)  # 3 points for 1st preference, 2 for 2nd, 1 for 3rd
        
        # Work center preference
        work_center_preference = employee.work_center_preferences.index(assignment.shift.work_center_id) + 1
        score += (len(employee.work_center_preferences) + 1 - work_center_preference)
        
        # Off-day preference (higher score for respecting off-day preferences)
        if is_off_day(employee, assignment.shift.start_time):
            score -= 5
    
    return score

def calculate_constraint_score(assignments):
    score = 0
    # Check for violations of constraints (e.g., working more than 5 consecutive days)
    # Subtract points for each violation
    return score

def calculate_fairness_score(assignments):
    employee_scores = {}
    for assignment in assignments:
        employee = assignment.shift.employee
        if employee.id not in employee_scores:
            employee_scores[employee.id] = 0
        
        # Add points for preferred shifts and work centers
        shift_index = (assignment.shift.start_time.hour - 6) // 8
        shift_preference = employee.shift_preferences.index(shift_index + 1) + 1
        employee_scores[employee.id] += (4 - shift_preference)
        
        work_center_preference = employee.work_center_preferences.index(assignment.shift.work_center_id) + 1
        employee_scores[employee.id] += (len(employee.work_center_preferences) + 1 - work_center_preference)
    
    # Calculate standard deviation of scores (lower is better)
    return -np.std(list(employee_scores.values()))

def crossover(parent1, parent2):
    mask = np.random.rand(*parent1.assignments.shape) < 0.5
    child = Schedule(parent1.assignments.shape[0], parent1.assignments.shape[1])
    child.assignments = np.where(mask, parent1.assignments, parent2.assignments)
    return child

def mutate(schedule, mutation_rate=0.01):
    mutation_mask = np.random.rand(*schedule.assignments.shape) < mutation_rate
    schedule.assignments = np.logical_xor(schedule.assignments, mutation_mask).astype(np.int8)
    return schedule
