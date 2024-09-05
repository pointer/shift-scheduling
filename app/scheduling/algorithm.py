import numpy as np
from app.scheduling.optimization import calculate_fitness, crossover, mutate
from datetime import datetime, timedelta
from typing import List, Dict
from app.db.models import Employee, WorkCenter, Shift, Schedule, ScheduleAssignment
from pulp import *
import random
from datetime import timedelta
from app.db.database import get_db

async def generate_schedule(start_date, end_date):
    async with get_db() as db:
        # Get all employees and work centers from the database
        employees = db.query(Employee).all()
        work_centers = db.query(WorkCenter).all()

        # Define sets
        K = range(1, len(set(e.category_id for e in employees)) + 1)
        Phi = {k: [e for e in employees if e.category_id == k] for k in K}
        Gamma = (end_date - start_date).days + 1
        Pi = range(1, len(work_centers) + 1)
        Lambda = range(1, 4)  # 3 shifts

        schedule = Schedule(start_date=start_date, end_date=end_date)
        assignments = []

        # Initial Step
        k = 1
        Phi_prime = Phi[1]
        Omega = set()
        P = 0

        while k <= len(K):
            model = create_hesm_model(k, Phi_prime, Gamma, Pi, Lambda, work_centers, assignments)
            status = model.solve()

            if status == LpStatusOptimal:
                new_assignments = extract_assignments(model, k, Phi_prime, Gamma, Pi, Lambda, start_date)
                assignments.extend(new_assignments)
                P += calculate_cost(new_assignments)
                
                # Update Omega and Phi_prime
                Omega.update(e.id for e in Phi_prime if any(a.shift.employee_id == e.id for a in new_assignments))
                Phi_prime = update_phi_prime(Phi, k, Omega)
                
                k += 1
            else:
                # If HESM_k is infeasible, implement heuristic
                heuristic_assignments = apply_heuristic(k, Phi_prime, Gamma, Pi, Lambda, work_centers, assignments)
                assignments.extend(heuristic_assignments)
                P += calculate_cost(heuristic_assignments)
                
                # Update Omega and Phi_prime
                Omega.update(e.id for e in Phi_prime if any(a.shift.employee_id == e.id for a in heuristic_assignments))
                Phi_prime = update_phi_prime(Phi, k, Omega)
                
                k += 1

        return schedule, assignments

def create_hesm_model(k, Phi_k, Gamma, Pi, Lambda, work_centers, existing_assignments):
    model = LpProblem(f"HESM_{k}", LpMinimize)
    
    # Define decision variables
    x = LpVariable.dicts("x", ((e.id, d, l, t) for e in Phi_k for d in range(Gamma) for l in Pi for t in Lambda), cat='Binary')
    w = LpVariable.dicts("w", (e.id for e in Phi_k), cat='Binary')
    z = LpVariable.dicts("z", ((e.id, d) for e in Phi_k for d in range(Gamma)), cat='Binary')
    v = LpVariable.dicts("v", (e.id for e in Phi_k), lowBound=0)

    # Define objective function
    obj_func = define_objective_function(k, Phi_k, x, w, z, v, Gamma, Pi, Lambda)
    model += obj_func

    # Add constraints
    add_constraints(model, k, Phi_k, x, w, z, v, Gamma, Pi, Lambda, work_centers, existing_assignments)

    return model

def extract_assignments(model, k, Phi_k, Gamma, Pi, Lambda, start_date):
    assignments = []
    for e in Phi_k:
        for d in range(Gamma):
            for l in Pi:
                for t in Lambda:
                    if value(model.variablesDict()[f"x_{e.id}_{d}_{l}_{t}"]) == 1:
                        shift_start = start_date + timedelta(days=d, hours=6 + (t-1)*8)
                        shift_end = shift_start + timedelta(hours=8)
                        shift = Shift(
                            start_time=shift_start,
                            end_time=shift_end,
                            employee_id=e.id,
                            work_center_id=l
                        )
                        assignments.append(ScheduleAssignment(shift=shift))
    return assignments

def calculate_cost(assignments):
    return sum(a.shift.employee.category.hourly_rate * 8 for a in assignments)

def update_phi_prime(Phi, k, Omega):
    return [e for e in Phi[k+1] if e.id not in Omega] if k+1 in Phi else []

def apply_heuristic(k, Phi_k, Gamma, Pi, Lambda, work_centers, existing_assignments):
    # Implement a simple heuristic to assign shifts when the HESM model is infeasible
    assignments = []
    for d in range(Gamma):
        for l in Pi:
            for t in Lambda:
                demand = work_centers[l-1].demand['weekday' if d % 7 < 5 else 'weekend'][str(k)][t-1]
                existing = sum(1 for a in existing_assignments if a.shift.start_time.date() == start_date + timedelta(days=d) and 
                               a.shift.work_center_id == l and (a.shift.start_time.hour - 6) // 8 == t - 1)
                needed = max(0, demand - existing)
                
                for _ in range(needed):
                    if Phi_k:
                        e = Phi_k.pop(0)  # Get the first available employee
                        shift_start = start_date + timedelta(days=d, hours=6 + (t-1)*8)
                        shift_end = shift_start + timedelta(hours=8)
                        shift = Shift(
                            start_time=shift_start,
                            end_time=shift_end,
                            employee_id=e.id,
                            work_center_id=l
                        )
                        assignments.append(ScheduleAssignment(shift=shift))
    return assignments

def define_objective_function(k, Phi_k, x, w, z, v, Gamma, Pi, Lambda):
    # Define preference parameters
    C1 = {(e.id, l, t): random.uniform(0, 1) for e in Phi_k for l in Pi for t in Lambda}
    C2 = {(e.id, l, t): random.uniform(0, 1) for e in Phi_k for l in Pi for t in Lambda}
    C3 = {(e.id, d): random.uniform(0, 1) for e in Phi_k for d in range(Gamma)}
    C_combined = {(e.id, l, t): C1[e.id, l, t] + C2[e.id, l, t] for e in Phi_k for l in Pi for t in Lambda}

    obj_func = (
        lpSum(e.category.hourly_rate * w[e.id] for e in Phi_k) +
        lpSum(C_combined[e.id, l, t] * x[e.id, d, l, t] for e in Phi_k for d in range(Gamma) for l in Pi for t in Lambda) +
        lpSum(C3[e.id, d] * (w[e.id] - z[e.id, d]) for e in Phi_k for d in range(Gamma)) +
        lpSum(v[e.id] for e in Phi_k)
    )
    return obj_func

def add_constraints(model, k, Phi_k, x, w, z, v, Gamma, Pi, Lambda, work_centers, existing_assignments):
    # Demand constraints
    for d in range(Gamma):
        for l in Pi:
            for t in Lambda:
                existing_demand = sum(1 for a in existing_assignments if a.shift.start_time.date() == start_date + timedelta(days=d) and 
                                      a.shift.work_center_id == l and (a.shift.start_time.hour - 6) // 8 == t - 1)
                if d % 7 < 5:  # Weekday
                    model += lpSum(x[e.id, d, l, t] for e in Phi_k) == work_centers[l-1].demand['weekday'][str(k)][t-1] - existing_demand
                else:  # Weekend
                    model += lpSum(x[e.id, d, l, t] for e in Phi_k) == work_centers[l-1].demand['weekend'][str(k)][t-1] - existing_demand

    # Constraint (C2.1): At most one shift per day for each employee
    for e in Phi_k:
        for d in range(Gamma):
            model += lpSum(x[e.id, d, l, t] for l in Pi for t in Lambda) <= w[e.id]

    # Constraint (C2.2): Maximum five shifts per week for each employee
    for e in Phi_k:
        for i in range(0, Gamma - 6):
            model += lpSum(x[e.id, d, l, t] for d in range(i, i+7) for l in Pi for t in Lambda) <= 5 * w[e.id]

    # Constraint (C2.3): Maximum five consecutive working days
    for e in Phi_k:
        for i in range(0, Gamma - 4):
            model += lpSum(x[e.id, d, l, t] for d in range(i, i+5) for l in Pi for t in Lambda) <= 5

    # Constraint (C2.4): Weekend off preference
    n_k = 2  # Assuming 2 weekends off for each category
    for e in Phi_k:
        model += lpSum(1 - lpSum(x[e.id, d, l, t] for l in Pi for t in Lambda) 
                       for d in range(Gamma) if d % 7 >= 5) >= n_k

    # Constraint (C2.5): Employee selection constraint
    for e in Phi_k:
        for d in range(Gamma):
            model += lpSum(x[e.id, d, l, t] for l in Pi for t in Lambda) <= w[e.id]

    # Constraint (C3): Avoiding consecutive shifts
    for e in Phi_k:
        for d in range(Gamma - 1):
            model += lpSum(x[e.id, d, l, t] for l in Pi for t in Lambda) + \
                     lpSum(x[e.id, d+1, l, t] for l in Pi for t in Lambda) <= 1

    # Constraint (C4.1): Delta calculation
    Delta_k = 20  # Example value, adjust as needed
    for e in Phi_k:
        model += v[e.id] >= lpSum(x[e.id, d, l, t] for d in range(Gamma) for l in Pi for t in Lambda) - Delta_k
        model += v[e.id] >= Delta_k - lpSum(x[e.id, d, l, t] for d in range(Gamma) for l in Pi for t in Lambda)

    # Symmetry-breaking constraints (as mentioned in point d)
    E_k = [(e1.id, e2.id) for e1 in Phi_k for e2 in Phi_k if e1.id < e2.id and 
           e1.shift_preferences == e2.shift_preferences and 
           e1.work_center_preferences == e2.work_center_preferences]
    
    for e1, e2 in E_k:
        model += lpSum(x[e1, d, l, t] for d in range(Gamma) for l in Pi for t in Lambda) >= \
                 lpSum(x[e2, d, l, t] for d in range(Gamma) for l in Pi for t in Lambda)

    return model
