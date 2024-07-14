import streamlit as st
import pandas as pd
import pyomo.environ as pyo

# Streamlit app title
st.title("Multiple-Allocation Problem with Interconnected Hubs")


# Optional file upload
uploaded_file = st.file_uploader("Upload Cost Matrix Excel file", type=["xlsx"])

if uploaded_file is not None:
    cost_df = pd.read_excel(uploaded_file)
else:

    # Load the data into a DataFrame
    # cost_df = pd.read_excel('Multi_Allocation_Hub_Location_Problem/cost_matrix_multi_hub.xlsx')
    cost_df = pd.read_excel('cost_matrix_multi_hub.xlsx')


# Load the data into a DataFrame
# cost_df = pd.DataFrame(cost_data)
cost_df.set_index('Unnamed: 0', inplace=True)
st.write("Cost Matrix:")
editable_cost_df = st.data_editor(cost_df)


# Transform the DataFrame into a dictionary for combined costs c(i, k, m, j)
cost = {}
nodes = list(editable_cost_df.index)
hubs = list(editable_cost_df.columns)
pairs = [(i, j) for i in nodes for j in nodes if i != j]
hub_pairs = [(k, m) for k in hubs for m in hubs if k != m]

for i in editable_cost_df.index:
    for j in editable_cost_df.index:
        if i != j:
            for k in editable_cost_df.columns:
                for m in editable_cost_df.columns:
                    if k != m:
                        cost[(i, k, m, j)] = editable_cost_df.loc[i, k] + editable_cost_df.loc[j, m]

# Initialize the model
model = pyo.ConcreteModel()

# Number of hubs to be used (modifiable via Streamlit)
p = st.slider("Number of hubs to be used", min_value=2, max_value=len(hubs), value=5)


if st.button('Calculate'):

    # Define sets
    model.pairs = pyo.Set(initialize=pairs, dimen=2)
    model.hub_pairs = pyo.Set(initialize=hub_pairs, dimen=2)
    model.hubs = pyo.Set(initialize=hubs)

    # Decision Variables
    model.x = pyo.Var(model.pairs, model.hub_pairs, within=pyo.Binary)
    model.y = pyo.Var(model.hubs, within=pyo.Binary)

    # Objective function: Minimize total cost
    def objective_rule(model):
        return sum(cost[(i, k, m, j)] * model.x[(i, j), (k, m)]
                for (i, j) in model.pairs for (k, m) in model.hub_pairs)

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    # Constraints
    # Total hubs constraint
    def total_hubs_constraint(model):
        return sum(model.y[k] for k in model.hubs) == p

    model.total_hubs_constraint = pyo.Constraint(rule=total_hubs_constraint)

    # Allocation constraint
    def allocation_constraint(model, i, j):
        return sum(model.x[(i, j), (k, m)] for (k, m) in model.hub_pairs) == 1

    model.allocation_constraint = pyo.Constraint(model.pairs, rule=allocation_constraint)

    # First flow constraint
    def flow_constraint_a(model, i, j, k):
        return sum(model.x[(i, j), (k, m)] for m in hubs if k != m) <= model.y[k]

    model.flow_constraint_a = pyo.Constraint(pairs, hubs, rule=flow_constraint_a)

    # Second flow constraint 
    def flow_constraint_b(model, i, j, m):
        return sum(model.x[(i, j), (k, m)] for k in hubs if m != k) <= model.y[m]

    model.flow_constraint_b = pyo.Constraint(pairs, hubs, rule=flow_constraint_b)

    # Non-negativity and binary constraints are implicit in the variable definitions

    # Solve the model
    # opt = pyo.SolverFactory('cbc', executable='Multi_Allocation_Hub_Location_Problem\\bin\\cbc.exe')  # Change solver if needed
    opt = pyo.SolverFactory('cbc', executable='bin\\cbc.exe')  # Change solver if needed
    results = opt.solve(model)

    # Extract the objective function value
    objective_value = pyo.value(model.obj)
    st.write("\nObjective Function Value:", objective_value)

    # Extract results
    allocation_plan = pd.DataFrame(
        [(i, j, k, m, pyo.value(model.x[(i, j), (k, m)])) for (i, j) in model.pairs for (k, m) in model.hub_pairs if pyo.value(model.x[(i, j), (k, m)]) > 0],
        columns=['Origin', 'Destination', 'First Hub', 'Second Hub', 'Allocation']
    )

    st.write("\nAllocation Plan Table")
    st.write(allocation_plan[['Origin', 'Destination', 'First Hub', 'Second Hub']])


# running note
# streamlit run multi_hub_app.py --server.enableXsrfProtection false