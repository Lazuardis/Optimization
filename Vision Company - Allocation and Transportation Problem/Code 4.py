import pyomo.environ as pyo
import pandas as pd

# Initialize model
model = pyo.ConcreteModel()

# Define sets
plants = [1, 2, 3]
products = ['Small', 'Medium', 'Large', 'Precision']
customers = ['RAYco', 'HONco', 'MMco']

# Define parameters
labor_hours = {
    1: {'Small': 3, 'Medium': 3, 'Large': 4, 'Precision': 4},
    2: {'Small': 3.5, 'Medium': 3.5, 'Large': 4.5, 'Precision': 4.5},
    3: {'Small': 3, 'Medium': 3.5, 'Large': 4, 'Precision': 4.5}
}

machine_hours = {
    1: {'Small': 8, 'Medium': 8.5, 'Large': 9, 'Precision': 9},
    2: {'Small': 7, 'Medium': 7, 'Large': 8, 'Precision': 9},
    3: {'Small': 7.5, 'Medium': 7.5, 'Large': 8.5, 'Precision': 8.5}
}

material = {
    1: {'Small': 1.0, 'Medium': 1.1, 'Large': 1.2, 'Precision': 1.3},
    2: {'Small': 1.1, 'Medium': 1.0, 'Large': 1.1, 'Precision': 1.4},
    3: {'Small': 1.1, 'Medium': 1.1, 'Large': 1.3, 'Precision': 1.3}
}

labor_capacity = {1: 6000, 2: 5000, 3: 3000}
machine_capacity = {1: 10000, 2: 12500, 3: 6000}
total_material = 3500

production_cost = {
    1: {'Small': 14, 'Medium': 16, 'Large': 18, 'Precision': 26},
    2: {'Small': 13, 'Medium': 17, 'Large': 20, 'Precision': 24},
    3: {'Small': 14, 'Medium': 15, 'Large': 19, 'Precision': 23}
}

sales_price = {
    'RAYco': {'Small': 17, 'Medium': 18, 'Large': 22, 'Precision': 29},
    'HONco': {'Small': 16, 'Medium': 18, 'Large': 22, 'Precision': 26},
    'MMco': {'Small': 16, 'Medium': 17, 'Large': 23, 'Precision': 27}
}

shipping_cost = {
    (1, 'RAYco'): 1.0, (1, 'HONco'): 1.6, (1, 'MMco'): 1.1,
    (2, 'RAYco'): 1.2, (2, 'HONco'): 1.5, (2, 'MMco'): 1.0,
    (3, 'RAYco'): 1.4, (3, 'HONco'): 1.5, (3, 'MMco'): 1.3
}

demand = {
    'RAYco': {'Small': 200, 'Medium': 300, 'Large': 500, 'Precision': 200},
    'HONco': {'Small': 400, 'Medium': 300, 'Large': 200, 'Precision': 400},
    'MMco': {'Small': 200, 'Medium': 400, 'Large': 300, 'Precision': 300}
}

inspection_capacity = 1500

# Decision Variables
model.prod = pyo.Var(plants, products, within=pyo.NonNegativeIntegers)
model.ship = pyo.Var(plants, products, customers, within=pyo.NonNegativeIntegers)

# Objective function: Maximize profit
def objective_rule(model):
    revenue = sum(model.ship[p, r, c] * sales_price[c][r] for p in plants for r in products for c in customers)
    production_costs = sum(model.prod[p, r] * production_cost[p][r] for p in plants for r in products)
    shipping_costs = sum(model.ship[p, r, c] * shipping_cost[(p, c)] for p in plants for r in products for c in customers)
    return revenue - production_costs - shipping_costs

model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

# Constraints
# Labor capacity constraints
def labor_constraint(model, p):
    return sum(model.prod[p, r] * labor_hours[p][r] for r in products) <= labor_capacity[p]
model.labor_constraint = pyo.Constraint(plants, rule=labor_constraint)

# Machine capacity constraints
def machine_constraint(model, p):
    return sum(model.prod[p, r] * machine_hours[p][r] for r in products) <= machine_capacity[p]
model.machine_constraint = pyo.Constraint(plants, rule=machine_constraint)

# Material constraints
def material_constraint(model):
    return sum(model.prod[p, r] * material[p][r] for p in plants for r in products) <= total_material
model.material_constraint = pyo.Constraint(rule=material_constraint)

# Demand satisfaction
def demand_constraint(model, c, r):
    return sum(model.ship[p, r, c] for p in plants) <= demand[c][r] 
model.demand_constraint = pyo.Constraint(customers, products, rule=demand_constraint)

# Production balance
def production_balance_constraint(model, p, r):
    return sum(model.ship[p, r, c] for c in customers) == model.prod[p, r]
model.production_balance_constraint = pyo.Constraint(plants, products, rule=production_balance_constraint)

# Special inspection capacity
def inspection_constraint(model):
    return sum(model.ship[p, r, c] for p in [1, 2] for r in products for c in ['RAYco', 'HONco']) <= inspection_capacity
model.inspection_constraint = pyo.Constraint(rule=inspection_constraint)

model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)

# Solve the model
# opt = pyo.SolverFactory('cbc', executable='C:\\bin\\cbc.exe')
opt = pyo.SolverFactory('IPOPT')
#opt = pyo.SolverFactory('gurobi')
results = opt.solve(model)
# model.pprint()


#display all duals
print("Duals for Machine Constraints")
for n, c in enumerate(model.component_objects(pyo.Constraint, active=True)):
    if n != 1: #print only machine constraint
        continue
   
    print("   Constraint", c)
    for index in c:
        print("      ", index, model.dual[c[index]])

# Extract results
production_plan = pd.DataFrame([(p, r, pyo.value(model.prod[p, r])) for p in plants for r in products], columns=['Plant', 'Product', 'Production'])
shipping_plan = pd.DataFrame([(p, r, c, pyo.value(model.ship[p, r, c])) for p in plants for r in products for c in customers], columns=['Plant', 'Product', 'Customer', 'Shipping'])

# print(production_plan)
# print(shipping_plan)

production_contingency_table = production_plan.pivot(index='Plant', columns='Product', values='Production')
shipping_contingency_table = shipping_plan.pivot_table(index=['Plant', 'Product'], columns='Customer', values='Shipping', aggfunc='sum')

# print("\nProduction Contingency Table")
# print(production_contingency_table)

# print("\nShipping Contingency Table")
# print(shipping_contingency_table)

print("Objective value:", pyo.value(model.obj))

# Calculate the cost and revenue generated from each plant
production_costs = production_plan.apply(lambda row: row['Production'] * production_cost[row['Plant']][row['Product']], axis=1)
shipping_costs = shipping_plan.apply(lambda row: row['Shipping'] * shipping_cost[(row['Plant'], row['Customer'])], axis=1)
revenues = shipping_plan.apply(lambda row: row['Shipping'] * sales_price[row['Customer']][row['Product']], axis=1)

# Sum production and shipping costs, and revenue for each plant
production_plan['Production Cost'] = production_costs
shipping_plan['Shipping Cost'] = shipping_costs
shipping_plan['Revenue'] = revenues

# Aggregate costs and revenue by plant
plant_production_cost = production_plan.groupby('Plant')['Production Cost'].sum()
plant_shipping_cost = shipping_plan.groupby('Plant')['Shipping Cost'].sum()
plant_revenue = shipping_plan.groupby('Plant')['Revenue'].sum()

# Calculate total cost and net revenue for each plant
plant_total_cost = plant_production_cost + plant_shipping_cost
plant_net_revenue = plant_revenue - plant_total_cost

# #Print the costs and revenues for each plant
# print("\nCosts and Revenues for Each Plant")
# for plant in plants:
#     print(f"Plant {plant}:")
#     print(f"  Production Cost: ${plant_production_cost[plant]:,.2f}")
#     print(f"  Shipping Cost: ${plant_shipping_cost[plant]:,.2f}")
#     print(f"  Total Cost: ${plant_total_cost[plant]:,.2f}")
#     print(f"  Revenue: ${plant_revenue[plant]:,.2f}")
#     print(f"  Net Revenue: ${plant_net_revenue[plant]:,.2f}\n")


# Following is the code to generate profit result by adding machine resource, one run per an additional resource.

import matplotlib.pyplot as plt

# Function to perform sensitivity analysis on machine hours
def machine_hours_sensitivity_analysis():
    sensitivity_results = {}
    
    for p in [3,1,2]:
        additional_hours = []
        profits = []
        
        for extra_hours in range(0, 200, 1):  # Example range from 0 to 3000 in increments of 100
            # Deactivate the existing machine constraint for plant p
            model.machine_constraint[p].deactivate()
            
            # Create a new constraint name
            constraint_name = f"machine_constraint_{p}"
            
            # Delete any existing constraint with the same name
            if hasattr(model, constraint_name):
                model.del_component(constraint_name)
            
            # Add the modified machine constraint for plant p
            model.add_component(constraint_name, pyo.Constraint(expr=sum(model.prod[p, r] * machine_hours[p][r] for r in products) <= machine_capacity[p] + extra_hours))
            
            # Reactivate the modified machine constraint for plant p
            getattr(model, constraint_name).activate()
            
            # Solve the model
            results = opt.solve(model)
            
            # Get the objective value (profit)
            profit = pyo.value(model.obj)
            
            # Store the additional hours and corresponding profit
            additional_hours.append(extra_hours)
            profits.append(profit)
        
        # Store results for plant p
        sensitivity_results[p] = {
            'additional_hours': additional_hours,
            'profits': profits
        }
        
        # Plot the results for plant p
        plt.plot(additional_hours, profits, marker='o', label=f'Plant {p}')
    
    plt.xlabel('Additional Machine Hours')
    plt.ylabel('Profit ($)')
    plt.title('Sensitivity Analysis: Profit vs Additional Machine Hours')
    plt.legend()
    plt.grid(True)
    plt.show()
    
    return sensitivity_results

# Perform the sensitivity analysis
sensitivity_results = machine_hours_sensitivity_analysis()

# Analyze marginal values for willingness to pay
for p in plants:
    additional_hours = sensitivity_results[p]['additional_hours']
    profits = sensitivity_results[p]['profits']
    
    marginal_values = [(profits[i+1] - profits[i]) / 1 for i in range(len(profits)-1)]
    optimal_hours_index = marginal_values.index(max(marginal_values))
    
    print(f"Plant {p}:")
    print(f"  Optimal additional machine hours: {additional_hours[optimal_hours_index]} hours")
    print(f"  Maximum willingness to pay per additional hour: ${max(marginal_values):,.2f}\n")
