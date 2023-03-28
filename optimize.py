import input
from ortools.sat.python import cp_model
import time

def runtime(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        seconds = round(time.time() - start, 2)
        print(f"Processing time {func.__name__}: {seconds} seconds")
        return result
    return wrapper if input.LOG_RUNTIME else func

@runtime
def create_var(model, num_players, num_country, num_league, num_clubs):
    '''Create the relevant variables'''
    # player[i] = 1 => i^th player is considered and 0 otherwise
    player = [model.NewBoolVar(f"player{i}") for i in range(num_players)]

    # These variables are basically chemistry of each club, league and nation
    z_club = [model.NewIntVar(0, 3, f"z_club{i}") for i in range(num_clubs)]
    z_league = [model.NewIntVar(0, 3, f"z_league{i}") for i in range(num_league)]
    z_nation = [model.NewIntVar(0, 3, f"z_nation{i}") for i in range(num_country)]

    # chem[i] = chemistry of i^th player
    chem = [model.NewIntVar(0, 3, f"chem{i}") for i in range(num_players)]

    # Needed for chemistry constraint
    b_c = [[model.NewBoolVar(f"b_c{j}{i}") for i in range(4)]for j in range(num_clubs)]
    b_l = [[model.NewBoolVar(f"b_l{j}{i}") for i in range(4)]for j in range(num_league)]
    b_n = [[model.NewBoolVar(f"b_n{j}{i}") for i in range(4)]for j in range(num_country)]

    # These variables represent whether a particular club, league or nation is
    # considered in the final solution or not
    club = [model.NewBoolVar(f"club_{i}") for i in range(num_clubs)]
    country = [model.NewBoolVar(f"country_{i}") for i in range(num_country)]
    league = [model.NewBoolVar(f"league_{i}") for i in range(num_league)]

    return model, player, chem, z_club, z_league, z_nation, b_c, b_l, b_n, club, country, league

@runtime
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

@runtime
def create_country_constraint(df, model, player):
    '''Create country constraint (>=)'''
    idxes = []
    for nation in input.COUNTRY:
        temp_idxes = list(df[df["Country"] == nation].index)
        idxes += temp_idxes
    expr = [player[j] for j in idxes]
    model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_COUNTRY)
    return model

@runtime
def create_league_constraint(df, model, player):
    '''Create league constraint (>=)'''
    idxes = []
    for league in input.LEAGUE:
        temp_idxes = list(df[df["League"] == league].index)
        idxes += temp_idxes
    expr = [player[j] for j in idxes]
    model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_LEAGUE)
    return model

@runtime
def create_club_constraint(df, model, player):
    '''Create club constraint (>=)'''
    idxes = []
    for club in input.CLUB:
        temp_idxes = list(df[df["Club"] == club].index)
        idxes += temp_idxes
    expr = [player[j] for j in idxes]
    model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_CLUB)
    return model

@runtime
def create_rarity_1_constraint(df, model, player):
    '''Create constraint for gold TOTW, gold Rare, gold Non Rare,
       silver TOTW, etc (>=).
    '''
    for i, rarity in enumerate(input.RARITY_1):
        idxes = list(df[(df["Color"] == rarity[0]) & (df["Rarity"] == rarity[1])].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_RARITY_1[i])
    return model

@runtime
def create_rarity_2_constraint(df, model, player):
    '''[Rare, Non Rare, TOTW, gold, silver, bronze ... etc] (>=).'''
    for i, rarity in enumerate(input.RARITY_2):
        col = "Rarity"
        if rarity in ["gold", "silver", "bronze"]:
            col = "Color"
        idxes = list(df[df[col] == rarity].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_RARITY_2[i])
    return model

@runtime
def create_squad_rating_constraint(df, model, player):
    '''Squad Rating (>=)'''
    rating = df["Rating"].tolist()
    model.Add(cp_model.LinearExpr.WeightedSum(player, rating) >= (input.SQUAD_RATING) * (input.NUM_PLAYERS))
    return model

@runtime
def create_min_overall_constraint(df, model, player):
    '''Minimum OVR of XX : Min X (>=)'''
    rating = df["Rating"].tolist()
    for i, rat in enumerate(input.MIN_OVERALL):
        idxes = list(df[df["Rating"] >= rat].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_MIN_OVERALL[i])
    return model

@runtime
def create_chemistry_constraint(df, model, chem, z_club, z_league, z_nation,
                                player, num_players, num_clubs, num_league, num_country,
                                country_dict, league_dict, club_dict, b_c, b_l, b_n):
    '''Optimize Chemistry (>=)
       Currently doesn't work for Icons and Heroes.
    '''

    players_grouped = {
        "Club": {}, "League": {}, "Country": {}
    }
    chem_expr = []
    for i in range(num_players):
        p_club, p_league, p_nation = df.loc[i, "Club"], df.loc[i, "League"], df.loc[i, "Country"]
        sum_expr = z_club[club_dict[p_club]] + z_league[league_dict[p_league]] + z_nation[country_dict[p_nation]]
        b = model.NewBoolVar(f"b{i}")
        model.Add(sum_expr <= 3).OnlyEnforceIf(b)
        model.Add(sum_expr > 3).OnlyEnforceIf(b.Not())
        model.Add(chem[i] == sum_expr).OnlyEnforceIf(b)
        model.Add(chem[i] == 3).OnlyEnforceIf(b.Not())
        curr_player = player[i]
        club_idx = club_dict[p_club]
        league_idx = league_dict[p_league]
        country_idx = country_dict[p_nation]
        players_grouped["Club"][club_idx] = players_grouped["Club"].get(club_idx, []) + [curr_player]
        players_grouped["League"][league_idx] = players_grouped["League"].get(league_idx, []) + [curr_player]
        players_grouped["Country"][country_idx] = players_grouped["Country"].get(country_idx, []) + [curr_player]

        model.Add(chem[i] >= input.CHEM_PER_PLAYER).OnlyEnforceIf(curr_player)

        player_chem_expr = model.NewIntVar(0, 3, f"obj_expr{i}") 
        chem_expr.append(player_chem_expr)
        model.AddMultiplicationEquality(player_chem_expr, curr_player, chem[i])


    for j in range(num_clubs):
        expr = players_grouped["Club"].get(j, [])
        sum_expr = cp_model.LinearExpr.Sum(expr)
        cons = [[0, 1], [2, 3], [4, 6], [7, input.NUM_PLAYERS]]
        for idx, num in enumerate (cons):
            lb, ub = cons[idx][0], cons[idx][1]
            model.AddLinearConstraint(sum_expr, lb, ub).OnlyEnforceIf(b_c[j][idx])
            model.Add(z_club[j] == idx).OnlyEnforceIf(b_c[j][idx])
        model.AddExactlyOne(b_c[j])
   
    for j in range(num_league):
        expr = players_grouped["League"].get(j, [])
        sum_expr = cp_model.LinearExpr.Sum(expr)
        cons = [[0, 2], [3, 4], [5, 7], [8, input.NUM_PLAYERS]]
        for idx, num in enumerate (cons):
            lb, ub = cons[idx][0], cons[idx][1]
            model.AddLinearConstraint(sum_expr, lb, ub).OnlyEnforceIf(b_l[j][idx])
            model.Add(z_league[j] == idx).OnlyEnforceIf(b_l[j][idx])
        model.AddExactlyOne(b_l[j])
       
    for j in range(num_country):
        expr = players_grouped["Country"].get(j, [])
        sum_expr = cp_model.LinearExpr.Sum(expr)
        cons = [[0, 1], [2, 4], [5, 7], [8, input.NUM_PLAYERS]]
        for idx, num in enumerate(cons):
            lb, ub = cons[idx][0], cons[idx][1]
            model.AddLinearConstraint(sum_expr, lb, ub).OnlyEnforceIf(b_n[j][idx])
            model.Add(z_nation[j] == idx).OnlyEnforceIf(b_n[j][idx])
        model.AddExactlyOne(b_n[j])
                           
     
    model.Add(cp_model.LinearExpr.Sum(chem_expr) >= input.CHEMISTRY)
    
    return model

@runtime
def create_max_club_constraint(df, model, player):
    '''Maximum player from same club (<=)'''
    club_list = df["Club"].unique()
    for club in club_list:
        idxes = list(df[df["Club"] == club].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) <= input.MAX_NUM_CLUB)
    return model

@runtime
def create_max_league_constraint(df, model, player):
    '''Maximum player from same league (<=)'''
    league_list = df["League"].unique()
    for league in league_list:
        idxes = list(df[df["League"] == league].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) <= input.MAX_NUM_LEAGUE)
    return model

@runtime
def create_max_country_constraint(df, model, player):
    '''Maximum player from same country (<=)'''
    country_list = df["Country"].unique()
    for country in country_list:
        idxes = list(df[df["Country"] == country].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) <= input.MAX_NUM_COUNTRY)
    return model

@runtime    
def create_min_club_constraint(df, model, player):
    '''Same Club Count: Min X (>=)'''
    club_list = df["Club"].unique()
    B_C = [model.NewBoolVar(f"B_C{i}") for i in range(len(club_list))]
    for i, club in enumerate(club_list):
        idxes = list(df[df["Club"] == club].index)
        expr = [player[j] for j in idxes]
        sum_expr = cp_model.LinearExpr.Sum(expr)
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.MIN_NUM_CLUB).OnlyEnforceIf(B_C[i])
        model.Add(cp_model.LinearExpr.Sum(expr) < input.MIN_NUM_CLUB).OnlyEnforceIf(B_C[i].Not())
    model.AddAtLeastOne(B_C)
    return model

@runtime
def create_min_league_constraint(df, model, player):
    '''Same League Count: Min X (>=)'''
    league_list = df["League"].unique()
    B_L = [model.NewBoolVar(f"B_L{i}") for i in range(len(league_list))]
    for i, league in enumerate(league_list):
        idxes = list(df[df["League"] == league].index)
        expr = [player[j] for j in idxes]
        sum_expr = cp_model.LinearExpr.Sum(expr)
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.MIN_NUM_LEAGUE).OnlyEnforceIf(B_L[i])
        model.Add(cp_model.LinearExpr.Sum(expr) < input.MIN_NUM_LEAGUE).OnlyEnforceIf(B_L[i].Not())
    model.AddAtLeastOne(B_L)
    return model

@runtime
def create_min_country_constraint(df, model, player):
    '''Same Nation Count: Min X (>=)'''
    country_list = df["Country"].unique()
    B_N = [model.NewBoolVar(f"B_N{i}") for i in range(len(country_list))]
    for i, country in enumerate(country_list):
        idxes = list(df[df["Country"] == country].index)
        expr = [player[j] for j in idxes]
        sum_expr = cp_model.LinearExpr.Sum(expr)
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.MIN_NUM_COUNTRY).OnlyEnforceIf(B_N[i])
        model.Add(cp_model.LinearExpr.Sum(expr) < input.MIN_NUM_COUNTRY).OnlyEnforceIf(B_N[i].Not())
    model.AddAtLeastOne(B_N)
    return model

@runtime
def create_unique_club_constraint(df, model, player, club):
    '''Clubs: Max/Min X'''
    club_list = df["Club"].unique()
    for i, Club in enumerate(club_list):
        idxes = list(df[df["Club"] == Club].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) >= 1).OnlyEnforceIf(club[i])
        model.Add(cp_model.LinearExpr.Sum(expr) == 0).OnlyEnforceIf(club[i].Not())
    model.Add(cp_model.LinearExpr.Sum(club) >= input.NUM_UNIQUE_CLUB)
    return model

@runtime
def create_unique_league_constraint(df, model, player, league):
    '''Leagues: Max/Min X'''
    league_list = df["League"].unique()
    for i, League in enumerate(league_list):
        idxes = list(df[df["League"] == League].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) >= 1).OnlyEnforceIf(league[i])
        model.Add(cp_model.LinearExpr.Sum(expr) == 0).OnlyEnforceIf(league[i].Not())
    model.Add(cp_model.LinearExpr.Sum(league) >= input.NUM_UNIQUE_LEAGUE)
    return model

@runtime
def create_unique_country_constraint(df, model, player, country):
    '''Nations: Max/Min X'''
    country_list = df["Country"].unique()
    for i, Country in enumerate(country_list):
        idxes = list(df[df["Country"] == Country].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) >= 1).OnlyEnforceIf(country[i])
        model.Add(cp_model.LinearExpr.Sum(expr) == 0).OnlyEnforceIf(country[i].Not())
    model.Add(cp_model.LinearExpr.Sum(country) >= input.NUM_UNIQUE_COUNTRY)
    return model

def set_objective(df, model, player):
    '''Set objective (minimize) based on cost'''
    cost = df["Cost"].tolist()
    model.Minimize(cp_model.LinearExpr.WeightedSum(player, cost))
    # set upper bound cost sum to 30000
    model.Add(cp_model.LinearExpr.WeightedSum(player, cost) <= 100000)
    return model

def get_dict(df, col):
   '''Map Club, League, Nation names to numbers'''
   d = {}
   unique_col = df[col].unique()
   for i, val in enumerate(unique_col):
    d[val] = i
   return d

@runtime
def SBC(df):
    '''Optimize SBC using Constraint Integer Programming'''
    num_players = df.shape[0]
    num_country = df.Country.nunique()
    num_league = df.League.nunique()
    num_clubs = df.Club.nunique()

    country_dict = get_dict(df, "Country")
    league_dict = get_dict(df, "League")
    club_dict = get_dict(df, "Club")
    
    '''Create the CP-SAT Model'''
    model = cp_model.CpModel()
    model, player, chem, z_club, z_league, z_nation, b_c, b_l, b_n, club, country, league = create_var(
        model, num_players, num_country, num_league, num_clubs)
    '''Essential constraints'''
    model = create_basic_constraints(df, model, player, num_players)
    '''Comment out the constraints not required'''
    #model = create_club_constraint(df, model, player)
    #model = create_league_constraint(df, model, player)
    #model = create_country_constraint(df, model, player)
    #model = create_squad_rating_constraint(df, model, player)
    #model = create_min_overall_constraint(df, model, player)
    model = create_max_club_constraint(df, model, player)
    #model = create_max_league_constraint(df, model, player)
    #model = create_max_country_constraint(df, model, player)
    #model = create_unique_club_constraint(df, model, player, club)
    model = create_unique_league_constraint(df, model, player, league)
    #model = create_unique_country_constraint(df, model, player, country)
    #model = create_min_club_constraint(df, model, player)
    #model = create_min_league_constraint(df, model, player)
    model = create_min_country_constraint(df, model, player)
    #model = create_rarity_1_constraint(df, model, player)
    model = create_rarity_2_constraint(df, model, player)
    '''Comment out the constraints not required'''

    '''If there is no constraint on total chemistry, simply set input.CHEMISTRY = 0
       instead of commenting out this constraint.
    '''
    
    model = create_chemistry_constraint(df, model, chem, z_club, z_league, z_nation,
                                        player, num_players, num_clubs, num_league, num_country,
                                        country_dict, league_dict, club_dict, b_c, b_l, b_n)
    '''Set objective based on player cost'''
    model = set_objective(df, model, player)

    '''Export Model to file'''
    # model.ExportToFile('model.txt')

    '''Solve'''
    print("Solve Started")
    solver = cp_model.CpSolver()
    
    '''Solver Parameters'''
    #solver.parameters.random_seed = 42
    solver.parameters.max_time_in_seconds = 50000
    #solver.parameters.log_search_progress = True
    # Specify the number of parallel workers (i.e. threads) to use during search (default = 8).
    # This should usually be lower than your number of available cpus + hyperthread in your machine.
    # Set to 16 or 24 if you have high-end CPU :).
    solver.parameters.num_search_workers = 6
    # solver.parameters.cp_model_presolve = False
    #solver.parameters.stop_after_first_solution = True 
    '''Solver Parameters'''
    
    status = solver.Solve(model)
    print(input.status_dict[status])
    print('\n')
    # assert (status == cp_model.OPTIMAL or status == cp_model.FEASIBLE)

    final_players = []
    final_chem = []
    df['Chemistry'] = 0 # We only care about chemistry of selected players
    for i in range(num_players):
        if solver.Value(player[i]) == 1:
            final_players.append(i)
            df.loc[i, "Chemistry"] = solver.Value(chem[i])

    return final_players

