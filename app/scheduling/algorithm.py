import numpy as np
from app.scheduling.optimization import calculate_fitness, crossover, mutate
from datetime import datetime, timedelta
from typing import List, Dict
from app.db.models import Employee, WorkCenter, Shift, Schedule, ScheduleAssignment
from pulp import *
import random
from datetime import timedelta

def generate_schedule(start_date, end_date):
    # Get all employees and work centers from the database
    db = next(get_db())
    employees = db.query(Employee).all()
    work_centers = db.query(WorkCenter).all()

    # Create the optimization model
    model = LpProblem("Shift_Scheduling", LpMaximize)

    # Define sets
    K = range(1, len(set(e.category_id for e in employees)) + 1)
    Phi = {k: [e for e in employees if e.category_id == k] for k in K}
    Gamma = (end_date - start_date).days + 1
    Pi = range(1, len(work_centers) + 1)
    Lambda = range(1, 4)  # 3 shifts

    # Define additional parameters
    n_k = {k: 2 for k in K}  # Example: 2 weekends off for each category

    # Define central preference value and bounds
    Delta_k = {k: random.uniform(13, 28 + 5 * len(Phi[k])) for k in K}
    Delta_min = 13
    Delta_max = 28 + 5 * max(len(Phi[k]) for k in K)

    # Define new decision variables
    v = LpVariable.dicts("v", ((k, e.id) for k in K for e in Phi[k]), lowBound=0)

    # Define preference parameters
    C1 = {(k, e.id, l, t): random.uniform(0, 1) for k in K for e in Phi[k] for l in Pi for t in Lambda}
    C2 = {(k, e.id, l, t): random.uniform(0, 1) for k in K for e in Phi[k] for l in Pi for t in Lambda}
    C3 = {(k, e.id, d): random.uniform(0, 1) for k in K for e in Phi[k] for d in range(Gamma)}

    # Calculate combined preference values
    C_combined = {(k, e.id, l, t): C1[k, e.id, l, t] + C2[k, e.id, l, t] for k in K for e in Phi[k] for l in Pi for t in Lambda}

    # Define decision variables
    x = LpVariable.dicts("x", ((k, e.id, d, l, t) for k in K for e in Phi[k] for d in range(Gamma) for l in Pi for t in Lambda), cat='Binary')
    w = LpVariable.dicts("w", ((k, e.id) for k in K for e in Phi[k]), cat='Binary')
    z = LpVariable.dicts("z", ((k, e.id, d) for k in K for e in Phi[k] for d in range(Gamma)), cat='Binary')
    f = LpVariable.dicts("f", ((i, d, k, l, t) for i in K for d in range(Gamma) for k in K for l in Pi for t in Lambda), lowBound=0, cat='Integer')

    # Demand requirements for weekdays and weekends
    for k in K:
        for d in range(Gamma):
            for l in Pi:
                for t in Lambda:
                    if d % 7 < 5:  # Weekday
                        model += lpSum(f[i, d, k, l, t] for i in range(1, k+1)) == work_centers[l-1].demand['weekday'][str(k)][t-1]
                    else:  # Weekend
                        model += lpSum(f[i, d, k, l, t] for i in range(1, k+1)) == work_centers[l-1].demand['weekend'][str(k)][t-1]

    # Assignment constraint
    for i in K:
        for d in range(Gamma):
            for l in Pi:
                for t in Lambda:
                    model += f[i, d, k, l, t] == lpSum(x[k, e.id, d, l, t] for k in range(i, len(K)+1) for e in Phi[k])

    # At most one shift per day for each employee (C2.1)
    for k in K:
        for e in Phi[k]:
            for d in range(Gamma):
                model += lpSum(x[k, e.id, d, l, t] for l in Pi for t in Lambda) == z[k, e.id, d]

    # Maximum five shifts per week for each employee (C2.2)
    for k in K:
        for e in Phi[k]:
            for i in range(0, Gamma - 6):
                model += lpSum(z[k, e.id, d] for d in range(i, i+7)) <= 5 * w[k, e.id]

    # Maximum five consecutive working days (C2.3)
    for k in K:
        for e in Phi[k]:
            for i in range(0, Gamma - 4):
                model += lpSum(z[k, e.id, d] for d in range(i, i+5)) <= 5 * w[k, e.id]

    # Weekend off preference (C2.4)
    for k in K:
        for e in Phi[k]:
            model += lpSum(1 - z[k, e.id, d] for d in range(Gamma) if d % 7 >= 5) >= n_k[k]

    # Employee selection constraint (C2.5)
    for k in K:
        for e in Phi[k]:
            for d in range(Gamma):
                model += z[k, e.id, d] <= w[k, e.id]

    # Avoiding consecutive shifts (C3)
    for k in K:
        for e in Phi[k]:
            for d in range(Gamma - 1):
                model += lpSum(x[k, e.id, d, l, t] for l in Pi for t in Lambda) + \
                         lpSum(x[k, e.id, d+1, l, t] for l in Pi for t in Lambda) <= w[k, e.id]

    # Define the objective function components
    preference_index = lpSum(C_combined[k, e.id, l, t] * x[k, e.id, d, l, t] for k in K for e in Phi[k] for d in range(Gamma) for l in Pi for t in Lambda)
    off_day_preference = lpSum(C3[k, e.id, d] * (w[k, e.id] - z[k, e.id, d]) for k in K for e in Phi[k] for d in range(Gamma))
    absolute_difference = lpSum(v[k, e.id] for k in K for e in Phi[k])

    # Set the objective to maximize the preference index and minimize the absolute difference
    model += 0.4 * preference_index + 0.4 * off_day_preference - 0.2 * absolute_difference

    # Add constraints for the absolute difference
    for k in K:
        for e in Phi[k]:
            model += v[k, e.id] >= Delta[k, e.id] - Delta_k[k]
            model += v[k, e.id] >= Delta_k[k] - Delta[k, e.id]

    # Solve the model
    model.solve()

    # Extract the solution and create the schedule
    schedule = Schedule(start_date=start_date, end_date=end_date)
    assignments = []

    for k in K:
        for e in Phi[k]:
            for d in range(Gamma):
                for l in Pi:
                    for t in Lambda:
                        if value(x[k, e.id, d, l, t]) == 1:
                            shift_start = start_date + timedelta(days=d, hours=6 + (t-1)*8)
                            shift_end = shift_start + timedelta(hours=8)
                            shift = Shift(
                                start_time=shift_start,
                                end_time=shift_end,
                                employee_id=e.id,
                                work_center_id=l
                            )
                            assignments.append(ScheduleAssignment(schedule=schedule, shift=shift))

    return schedule, assignments

# The rest of the file remains unchanged
def initialize_population(start_date, end_date, employees, work_centers):
    population = []
    for _ in range(POPULATION_SIZE):
        schedule, assignments = create_initial_schedule(start_date, end_date, employees, work_centers)
        population.append((schedule, assignments))
    return population

def create_initial_schedule(start_date: datetime, end_date: datetime, employees: List[Employee], work_centers: List[WorkCenter]):
    schedule = Schedule(start_date=start_date, end_date=end_date)
    assignments = []
    
    current_date = start_date
    while current_date <= end_date:
        for employee in employees:
            # Check if employee has worked for 5 consecutive days
            if has_worked_five_consecutive_days(employee, assignments, current_date):
                continue
            
            # Check if it's an off-day for the employee
            if is_off_day(employee, current_date):
                continue
            
            # Assign shift based on preferences and availability
            shift = assign_shift(employee, work_centers, current_date)
            if shift:
                assignments.append(ScheduleAssignment(schedule=schedule, shift=shift))
        
        current_date += timedelta(days=1)
    
    return schedule, assignments

def has_worked_five_consecutive_days(employee: Employee, assignments: List[ScheduleAssignment], current_date: datetime) -> bool:
    consecutive_days = 0
    for i in range(5):
        check_date = current_date - timedelta(days=i)
        if any(a.shift.employee_id == employee.id and a.shift.start_time.date() == check_date.date() for a in assignments):
            consecutive_days += 1
        else:
            break
    return consecutive_days == 5

def is_off_day(employee: Employee, current_date: datetime) -> bool:
    day_of_week = current_date.strftime("%A")
    return employee.off_day_preferences[day_of_week] <= 2  # Assuming 1 and 2 are the two preferred off-days

def assign_shift(employee: Employee, work_centers: List[WorkCenter], current_date: datetime) -> Shift:
    for shift_preference in employee.shift_preferences:
        for work_center_preference in employee.work_center_preferences:
            work_center = next((wc for wc in work_centers if wc.id == work_center_preference), None)
            if work_center:
                shift_start = current_date.replace(hour=6 + (shift_preference - 1) * 8, minute=0, second=0, microsecond=0)
                shift_end = shift_start + timedelta(hours=8)
                return Shift(
                    start_time=shift_start,
                    end_time=shift_end,
                    employee_id=employee.id,
                    work_center_id=work_center.id
                )
    return None  # No suitable shift found

def select_parents(population, fitness_scores):
    # Implementation of parent selection (e.g., tournament selection)
    pass
