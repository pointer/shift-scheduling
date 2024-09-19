import numpy as np
from app.scheduling.optimization import calculate_fitness, crossover, mutate
from datetime import date, datetime, timedelta
from typing import List, Dict, Union
from app.db.models import Employee, WorkCenter, Shift, Schedule, ScheduleAssignment, GeneratedSchedule
from pulp import *
from icecream import ic
import random
from datetime import timedelta
from app.db.database import get_db
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import traceback
import sys
import logging
from app.custom_encoder import custom_jsonable_encoder

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

MAX_RECURSION_DEPTH = 1000  # Adjust this value as needed

def is_preferred_work_center(employee, work_center):
    return work_center.id in employee.work_center_preferences

async def generate_schedule(db_session: AsyncSession, start_date: Union[date, datetime], end_date: Union[date, datetime], recursion_depth: int = 0):
    if recursion_depth > MAX_RECURSION_DEPTH:
        logger.error(f"Maximum recursion depth ({MAX_RECURSION_DEPTH}) exceeded")
        raise RecursionError("Maximum recursion depth exceeded")

    try:
        logger.debug(f"Generating schedule (depth: {recursion_depth})")
        # Convert to date if datetime is provided
        start_date = start_date.date() if isinstance(start_date, datetime) else start_date
        end_date = end_date.date() if isinstance(end_date, datetime) else end_date

        # Fetch employees without using selectinload
        employees_query = select(Employee)
        employees = (await db_session.execute(employees_query)).scalars().all()

        # Log work center preferences for each employee
        for employee in employees:
            logger.debug(f"Employee {employee.id} work center preferences: {employee.work_center_preferences}")

        # Fetch work centers
        work_centers_query = select(WorkCenter)
        work_centers = (await db_session.execute(work_centers_query)).scalars().all()

        # Define sets
        K = range(1, len(set(e.category_id for e in employees)) + 1)
        Phi = {k: [e for e in employees if e.category_id == k] for k in K}
        Gamma = (end_date - start_date).days + 1
        Pi = range(1, len(work_centers) + 1)
        Lambda = range(1, 4)  # 3 shifts

        schedule = Schedule(start_date=start_date, end_date=end_date)
        db_session.add(schedule)
        try:
            await db_session.flush()
        except Exception as e:
            logger.exception("Error flushing schedule to database")
            await db_session.rollback()
            raise

        assignments = []

        # Initial Step
        k = 1
        Phi_prime = Phi[1]
        Omega = set()
        P = 0

        while k <= len(K):
            logger.debug(f"Processing category {k}")
            model = create_hesm_model(k, Phi_prime, Gamma, Pi, Lambda, work_centers, assignments, start_date)
            status = model.solve()

            if status == LpStatusOptimal:
                logger.debug(f"Optimal solution found for category {k}")
                new_assignments = extract_assignments(model, k, Phi_prime, Gamma, Pi, Lambda, start_date, schedule)
                for assignment in new_assignments:
                    db_session.add(assignment)
                assignments.extend(new_assignments)
                P += calculate_cost(new_assignments)
                
                # Update Omega and Phi_prime
                Omega.update(e.id for e in Phi_prime if any(a.shift.employee_id == e.id for a in new_assignments))
                Phi_prime = update_phi_prime(Phi, k, Omega)
                
                k += 1
            else:
                logger.debug(f"No optimal solution found for category {k}, applying heuristic")
                heuristic_assignments = apply_heuristic(k, Phi_prime, Gamma, Pi, Lambda, work_centers, assignments, start_date, schedule)
                for assignment in heuristic_assignments:
                    db_session.add(assignment)
                assignments.extend(heuristic_assignments)
                P += calculate_cost(heuristic_assignments)
                
                # Update Omega and Phi_prime
                Omega.update(e.id for e in Phi_prime if any(a.shift.employee_id == e.id for a in heuristic_assignments))
                Phi_prime = update_phi_prime(Phi, k, Omega)
                
                k += 1
        # Save generated schedule
        for assignment in assignments:
            generated_schedule = GeneratedSchedule(\
                schedule_id=schedule.id,\
                employee_id=assignment.shift.employee_id,\
                work_center_id=assignment.shift.work_center_id,\
                shift_start=assignment.shift.start_time,\
                shift_end=assignment.shift.end_time
            )
            db_session.add(generated_schedule)
        
        try:
            await db_session.commit()
        except Exception as e:
            logger.exception("Error committing generated schedule to database")
            await db_session.rollback()
            raise

        return schedule, assignments

    except TypeError as e:
        logger.exception(f"TypeError in generate_schedule (depth: {recursion_depth})")
        await db_session.rollback()
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in generate_schedule (depth: {recursion_depth})")
        await db_session.rollback()
        raise

def create_hesm_model(k, Phi_k, Gamma, Pi, Lambda, work_centers, existing_assignments, start_date):
    model = LpProblem(f"HESM_{k}", LpMinimize)
    #ic('create_hesm_model === Start')
    
    # Define decision variables
    x = LpVariable.dicts("x", ((e.id, d, l, t) for e in Phi_k for d in range(Gamma) for l in Pi for t in Lambda), cat='Binary')
    w = LpVariable.dicts("w", ((e.id, wc.id) for e in Phi_k for wc in work_centers), cat='Binary')
    z = LpVariable.dicts("z", ((e.id, d) for e in Phi_k for d in range(Gamma)), cat='Binary')
    v = LpVariable.dicts("v", (e.id for e in Phi_k), lowBound=0)

    # Define preference parameters
    C1 = {(e.id, l, t): random.uniform(0, 1) for e in Phi_k for l in Pi for t in Lambda}
    C2 = {(e.id, l, t): random.uniform(0, 1) for e in Phi_k for l in Pi for t in Lambda}
    C3 = {(e.id, d): random.uniform(0, 1) for e in Phi_k for d in range(Gamma)}
    C_combined = {(e.id, l, t): C1[e.id, l, t] + C2[e.id, l, t] for e in Phi_k for l in Pi for t in Lambda}

    # Modify the objective function to heavily penalize non-preferred work centers
    obj_func = (
        lpSum(e.category.hourly_rate * w[e.id, wc.id] for e in Phi_k for wc in work_centers) +
        lpSum(1000 * w[e.id, wc.id] * (1 if wc.id not in e.work_center_preferences else 0) for e in Phi_k for wc in work_centers) +
        lpSum(C_combined[e.id, l, t] * x[e.id, d, l, t] for e in Phi_k for d in range(Gamma) for l in Pi for t in Lambda) +
        lpSum(C3[e.id, d] * (w[e.id, wc.id] - z[e.id, d]) for e in Phi_k for d in range(Gamma) for wc in work_centers) +
        lpSum(v[e.id] for e in Phi_k)
    )
    model += obj_func

    # Add constraints
    add_constraints(model, k, Phi_k, x, w, z, v, Gamma, Pi, Lambda, work_centers, existing_assignments, start_date)

    #ic('create_hesm_model === End')
    return model

def extract_assignments(model, k, Phi_k, Gamma, Pi, Lambda, start_date, schedule):
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
                        assignment = ScheduleAssignment(shift=shift, schedule=schedule)
                        assignment.shift.employee = e  # Ensure the employee is set
                        assignments.append(assignment)
    return assignments

def calculate_cost(assignments):
    total_cost = 0
    for a in assignments:
        if a.shift and a.shift.employee and a.shift.employee.category:
            total_cost += a.shift.employee.category.hourly_rate * 8
    return total_cost

def update_phi_prime(Phi, k, Omega):
    logger.debug(f"Updating Phi_prime for k={k}")
    if k+1 in Phi:
        return [e for e in Phi[k+1] if e.id not in Omega]
    else:
        logger.debug(f"No more categories after {k}")
        return []
    #ic('update_phi_prime ===End')

def apply_heuristic(k, Phi_k, Gamma, Pi, Lambda, work_centers, existing_assignments, start_date, schedule):
    logger.debug(f"Applying heuristic for category {k}")
    assignments = []
    #ic('apply_heuristic ===Start')   
    for d in range(Gamma):
        for l in Pi:
            for t in Lambda:
                demand = work_centers[l-1].demand['weekday' if d % 7 < 5 else 'weekend'][str(k)][t-1]
                existing = sum(1 for a in existing_assignments 
                               if isinstance(a.shift.start_time, datetime) and
                               (a.shift.start_time.date() == start_date + timedelta(days=d)) and 
                               (a.shift.work_center_id == l) and 
                               ((a.shift.start_time.hour - 6) // 8 == t - 1))
                needed = max(0, demand - existing)
                
                for _ in range(needed):
                    if Phi_k:
                        # Find an employee with the current work center in their preferences
                        suitable_employees = [e for e in Phi_k if work_centers[l-1].id in e.work_center_preferences]
                        
                        if suitable_employees:
                            e = suitable_employees.pop(0)
                            Phi_k.remove(e)
                            logger.debug(f"Assigning employee {e.id} to preferred work center {work_centers[l-1].id}")
                        else:
                            logger.debug(f"No suitable employee found for work center {work_centers[l-1].id}")
                            continue  # Skip this assignment if no suitable employee is found
                        
                        shift_start = datetime.combine(start_date + timedelta(days=d), datetime.min.time()) + timedelta(hours=6 + (t-1)*8)
                        shift_end = shift_start + timedelta(hours=8)
                        shift = Shift(
                            start_time=shift_start,
                            end_time=shift_end,
                            employee_id=e.id,
                            work_center_id=work_centers[l-1].id
                        )
                        assignment = ScheduleAssignment(shift=shift, schedule=schedule)
                        assignment.shift.employee = e  # Ensure the employee is set
                        assignments.append(assignment)
                    else:
                        logger.debug(f"No more employees available for category {k}")
                        break
                
                if not Phi_k:
                    break
            if not Phi_k:
                break
        if not Phi_k:
            break
    #ic('apply_heuristic ===End')    
    return assignments

def define_objective_function(k, Phi_k, x, w, z, v, Gamma, Pi, Lambda):
    # Define preference parameters
    C1 = {(e.id, l, t): random.uniform(0, 1) for e in Phi_k for l in Pi for t in Lambda}
    C2 = {(e.id, l, t): random.uniform(0, 1) for e in Phi_k for l in Pi for t in Lambda}
    C3 = {(e.id, d): random.uniform(0, 1) for e in Phi_k for d in range(Gamma)}
    C_combined = {(e.id, l, t): C1[e.id, l, t] + C2[e.id, l, t] for e in Phi_k for l in Pi for t in Lambda}
    #ic('define_objective_function ===Start')
    obj_func = (
        lpSum(e.category.hourly_rate * w[e.id] for e in Phi_k) +
        lpSum(C_combined[e.id, l, t] * x[e.id, d, l, t] for e in Phi_k for d in range(Gamma) for l in Pi for t in Lambda) +
        lpSum(C3[e.id, d] * (w[e.id] - z[e.id, d]) for e in Phi_k for d in range(Gamma)) +
        lpSum(v[e.id] for e in Phi_k)
    )
    #ic('define_objective_function ===End')
    return obj_func

def add_constraints(model, k, Phi_k, x, w, z, v, Gamma, Pi, Lambda, work_centers, existing_assignments, start_date):
    try:
        #ic('add_constraints ===start')
        for d in range(Gamma):
            for l in Pi:
                for t in Lambda:
                    # Convert start_date to datetime for comparison
                    start_datetime = datetime.combine(start_date, datetime.min.time())
                    existing_demand = sum(1 for a in existing_assignments 
                                          if isinstance(a.shift.start_time, datetime) and
                                          a.shift.start_time.date() == start_date + timedelta(days=d) and 
                                          a.shift.work_center_id == l and 
                                          (a.shift.start_time.hour - 6) // 8 == t - 1)
                    
                    # Check if work_center exists and has demand data
                    if l-1 < len(work_centers) and work_centers[l-1] is not None and work_centers[l-1].demand is not None:
                        if d % 7 < 5:  # Weekday
                            if 'weekday' in work_centers[l-1].demand and str(k) in work_centers[l-1].demand['weekday']:
                                model += lpSum(x[e.id, d, l, t] for e in Phi_k) == work_centers[l-1].demand['weekday'][str(k)][t-1] - existing_demand
                            else:
                                logger.warning(f"Missing weekday demand data for work center {l}, category {k}, shift {t}")
                        else:  # Weekend
                            if 'weekend' in work_centers[l-1].demand and str(k) in work_centers[l-1].demand['weekend']:
                                model += lpSum(x[e.id, d, l, t] for e in Phi_k) == work_centers[l-1].demand['weekend'][str(k)][t-1] - existing_demand
                            else:
                                logger.warning(f"Missing weekend demand data for work center {l}, category {k}, shift {t}")
                    else:
                        logger.warning(f"Invalid work center index or missing demand data: {l-1}")

        # Constraint (C2.1): At most one shift per day for each employee
        for e in Phi_k:
            for d in range(Gamma):
                model += lpSum(x[e.id, d, l, t] for l in Pi for t in Lambda) <= lpSum(w[e.id, wc.id] for wc in work_centers)

        # Constraint (C2.2): Maximum five shifts per week for each employee
        for e in Phi_k:
            for i in range(0, Gamma - 6):
                model += lpSum(x[e.id, d, l, t] for d in range(i, i+7) for l in Pi for t in Lambda) <= 5 * lpSum(w[e.id, wc.id] for wc in work_centers)

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
            model += lpSum(w[e.id, wc.id] for wc in work_centers) <= 1

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

        # New constraint: Ensure x variables are consistent with w variables
        for e in Phi_k:
            for d in range(Gamma):
                for l in Pi:
                    for t in Lambda:
                        model += x[e.id, d, l, t] <= w[e.id, work_centers[l-1].id]

        # Add constraint to ensure employees are only assigned to preferred work centers
        for e in Phi_k:
            for wc in work_centers:
                if wc.id not in e.work_center_preferences:
                    model += w[e.id, wc.id] == 0

        #ic('add_constraints ===End')
        return model
    except Exception as e:
        logger.exception("Error in add_constraints")
        raise
