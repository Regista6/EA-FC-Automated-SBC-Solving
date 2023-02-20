import input
from ortools.sat.python import cp_model

def create_var(model, num_players, num_country, num_league, num_clubs):
    '''Create the relevant variables'''
    # player[i] = 1 => i^th player is considered and 0 otherwise
    player = [model.NewBoolVar(f"player{i}") for i in range(num_players)]

    # These variables are basically chemistry of each club, league and nation
    z_club = [model.NewIntVar(0, 3, f"z_club{i}") for i in range(num_clubs)]
    z_league = [model.NewIntVar(0, 3, f"z_league{i}") for i in range(num_league)]
    z_nation = [model.NewIntVar(0, 3, f"z_nation{i}") for i in range(num_country)]
    
    # chem[i] = chemistry of i^th player
    chem = [model.NewIntVar(input.CHEM_PER_PLAYER, 3, f"chem{i}") for i in range(num_players)]

    return model, player, chem, z_club, z_league, z_nation

def create_basic_constraints(df, model, player, num_players):
    '''Create some essential constraints'''
    # Max players in squad
    model.Add(cp_model.LinearExpr.Sum(player) == input.NUM_PLAYERS)
    
    # Unique players constraint. Currently different players of same name not present in dataset.
    # Same player with multiple card versions present.
    mark_name = {}
    for i in range(num_players):
        name = df.loc[i, "Name"]
        if name in mark_name:
            continue
        mark_name[name] = 1 
        idxes = list(df[df["Name"] == name].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) <= 1)

    # Formation constraint
    if input.FIX_PLAYERS == 1:
        mark_pos = {}
        formation_list = input.formation_dict[input.FORMATION]
        for pos in formation_list:
            if pos in mark_pos:
                continue
            mark_pos[pos] = 1
            idxes = list(df[df["Position"] == pos].index)
            cnt = formation_list.count(pos)
            expr = [player[j] for j in idxes]
            model.Add(cp_model.LinearExpr.Sum(expr) == cnt)
    return model

def create_country_constraint(df, model, player):
    '''Create country constraint (>=)'''
    idxes = []
    for nation in input.COUNTRY:
        temp_idxes = list(df[df["Country"] == nation].index)
        idxes += temp_idxes
    expr = [player[j] for j in idxes]
    model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_COUNTRY)
    return model

def create_league_constraint(df, model, player):
    '''Create league constraint (>=)'''
    idxes = []
    for league in input.LEAGUE:
        temp_idxes = list(df[df["League"] == league].index)
        idxes += temp_idxes
    expr = [player[j] for j in idxes]
    model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_LEAGUE)
    return model

def create_club_constraint(df, model, player):
    '''Create club constraint (>=)'''
    idxes = []
    for club in input.CLUB:
        temp_idxes = list(df[df["Club"] == club].index)
        idxes += temp_idxes
    expr = [player[j] for j in idxes]
    model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_CLUB)
    return model

def create_rarity_1_constraint(df, model, player):
    '''Create constraint for gold TOTW, gold Rare, gold Non Rare,
       silver TOTW, etc (>=).
    '''
    for i, rarity in enumerate(input.RARITY_1):
        idxes = list(df[(df["Color"] == rarity[0]) & (df["Rarity"] == rarity[1])].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_RARITY_1[i])
    return model

def create_squad_rating_constraint(df, model, player):
    '''Squad Rating (>=)'''
    rating = df["Rating"].tolist()
    model.Add(cp_model.LinearExpr.WeightedSum(player, rating) >= (input.SQUAD_RATING) * (input.NUM_PLAYERS))
    return model

def create_min_overall_constraint(df, model, player):
    '''Minimum OVR of XX : Min X (>=)'''
    rating = df["Rating"].tolist()
    for i, rat in enumerate(input.MIN_OVERALL):
        idxes = list(df[df["Rating"] >= rat].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_MIN_OVERALL[i])
    return model

def create_chemistry_constraint(df, model, chem, z_club, z_league, z_nation, 
                                player, num_players, num_clubs, num_league, num_country, 
                                country_dict, league_dict, club_dict):
    '''Optimize Chemistry (>=)
       Currently doesn't work for Icons and Heroes.
    '''
    for i in range(num_players):
        p_club, p_league, p_nation = df.loc[i, "Club"], df.loc[i, "League"], df.loc[i, "Country"]
        expr = z_club[club_dict[p_club]] + z_league[league_dict[p_league]] + z_nation[country_dict[p_nation]]
        b = model.NewBoolVar(f"b{i}")
        model.Add(expr <= 3).OnlyEnforceIf(b)
        model.Add(expr == 3).OnlyEnforceIf(b.Not())
        model.Add(chem[i] == expr)

    for j in range(num_clubs):
        expr = []
        for i in range(num_players):
            idx = club_dict[df.loc[i, "Club"]]
            if idx == j:
                expr.append(player[i])
        sum_expr = cp_model.LinearExpr.Sum(expr)
        cons = [[0, 1], [2, 3], [4, 6], [7, input.NUM_PLAYERS]]
        B  = [model.NewBoolVar(f"b_c{j}{i}") for i in range(4)]
        for idx, num in enumerate (cons):
            lb, ub = cons[idx][0], cons[idx][1]
            model.AddLinearConstraint(sum_expr, lb, ub).OnlyEnforceIf(B[idx])
            model.Add(z_club[j] == idx).OnlyEnforceIf(B[idx])
        model.AddExactlyOne(B)
    
    for j in range(num_league):
        expr = []
        for i in range(num_players):
            idx = league_dict[df.loc[i, "League"]]
            if idx == j:
                expr.append(player[i])
        sum_expr = cp_model.LinearExpr.Sum(expr)
        cons = [[0, 2], [3, 4], [5, 7], [8, input.NUM_PLAYERS]]
        B  = [model.NewBoolVar(f"b_l{j}{i}") for i in range(4)]
        for idx, num in enumerate (cons):
            lb, ub = cons[idx][0], cons[idx][1]
            b = B[idx]
            model.AddLinearConstraint(sum_expr, lb, ub).OnlyEnforceIf(b)
            model.Add(z_league[j] == idx).OnlyEnforceIf(b)
        model.AddExactlyOne(B)

    for j in range(num_country):
        expr = []
        for i in range(num_players):
            idx = country_dict[df.loc[i, "Country"]]
            if idx == j:
                expr.append(player[i])
        sum_expr = cp_model.LinearExpr.Sum(expr)
        cons = [[0, 1], [2, 4], [5, 7], [8, input.NUM_PLAYERS]]
        B = [model.NewBoolVar(f"b_n{j}{i}") for i in range(4)]
        for idx, num in enumerate(cons):
            lb, ub = cons[idx][0], cons[idx][1]
            b = B[idx]
            model.AddLinearConstraint(sum_expr, lb, ub).OnlyEnforceIf(b)
            model.Add(z_nation[j] == idx).OnlyEnforceIf(b)
        model.AddExactlyOne(B)

    chem_expr = [model.NewIntVar(0, 3, f"obj_expr{i}") for i in range(num_players)]

    for i in range(num_players):
        model.AddMultiplicationEquality(chem_expr[i], player[i], chem[i])

    model.Add(cp_model.LinearExpr.Sum(chem_expr) >= input.CHEMISTRY)
    return model

def create_max_club_constraint(df, model, player):
    '''Maximum player from same club (<=)'''
    club_list = df["Club"].unique()
    for club in club_list:
        idxes = list(df[df["Club"] == club].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) <= input.MAX_NUM_CLUB)
    return model

def create_max_league_constraint(df, model, player):
    '''Maximum player from same league (<=)'''
    league_list = df["League"].unique()
    for league in league_list:
        idxes = list(df[df["League"] == league].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) <= input.MAX_NUM_LEAGUE)
    return model

def create_max_country_constraint(df, model, player):
    '''Maximum player from same country (<=)'''
    country_list = df["Country"].unique()
    for country in country_list:
        idxes = list(df[df["Country"] == country].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) <= input.MAX_NUM_COUNTRY)
    return model

def create_rarity_2_constraint(df, model, player):
    '''[Rare, Non Rare, TOTW ... etc] (>=).'''
    for i, rarity in enumerate(input.RARITY_2):
        idxes = list(df[df["Rarity"] == rarity].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_RARITY_2[i])
    return model

def set_objective(df, model, player):
    '''Set objective (minimize) based on cost'''
    cost = df["Cost"].tolist()
    model.Minimize(cp_model.LinearExpr.WeightedSum(player, cost))
    return model

def get_dict(df, col):
   '''Map Club, League, Nation names to numbers'''
   d = {}
   unique_col = df[col].unique()
   for i, val in enumerate(unique_col):
    d[val] = i
   return d

def SBC(df):
    '''Optimize SBC using Constraint Programming'''
    num_players = df.shape[0]
    num_country = df.Country.nunique()
    num_league = df.League.nunique()
    num_clubs = df.Club.nunique()

    country_dict = get_dict(df, "Country")
    league_dict = get_dict(df, "League")
    club_dict = get_dict(df, "Club")

    '''Create the CP-SAT Model'''
    model = cp_model.CpModel()

    model, player, chem, z_club, z_league, z_nation = create_var(model, num_players, num_country, num_league, num_clubs)

    '''Essential constraints'''
    model = create_basic_constraints(df, model, player, num_players)

    '''Comment out the constraints not required'''
    #model = create_country_constraint(df, model, player)
    model = create_league_constraint(df, model, player)
    #model = create_club_constraint(df, model, player)
    #model = create_rarity_1_constraint(df, model, player)
    model = create_squad_rating_constraint(df, model, player)
    #model = create_min_overall_constraint(df, model, player)
    model = create_max_club_constraint(df, model, player)
    #model = create_max_league_constraint(df, model, player)
    #model = create_max_country_constraint(df, model, player)
    model = create_rarity_2_constraint(df, model, player)
    '''Comment out the constraints not required'''

    '''If there is no constraint on total chemistry, simply set input.CHEMISTRY = 0
       instead of commenting out this constraint.
    '''
    model = create_chemistry_constraint(df, model, chem, z_club, z_league, z_nation, 
                                        player, num_players, num_clubs, num_league, num_country, 
                                        country_dict, league_dict, club_dict)
    
    '''Set objective based on player cost'''
    model = set_objective(df, model, player)

    '''Solve'''
    print("Solve Started")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 100.0
    status = solver.Solve(model)
    assert (status == cp_model.OPTIMAL or status == cp_model.FEASIBLE)
    
    if status == cp_model.OPTIMAL:
        print("Solution is Optimal !!. ")
    elif status == cp_model.FEASIBLE:
        print("Solution is not Optimal. Instead feasible soln. produced.")
        
    final_players = []
    final_chem = []
    df['Chemistry'] = 0 # We only care about chemistry of selected players
    for i in range(num_players):
        if solver.Value(player[i]) == 1:
            final_players.append(i)
            df.loc[i, "Chemistry"] = solver.Value(chem[i])
    return final_players
