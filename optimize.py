import input
import time
from ortools.sat.python import cp_model

def runtime(func):
    '''Wrapper function to log the execution time'''
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        seconds = round(time.time() - start, 2)
        print(f"Processing time {func.__name__}: {seconds} seconds")
        return result
    return wrapper if input.LOG_RUNTIME else func

@runtime
def create_var(model, df, map_idx, num_cnts):
    '''Create the relevant variables'''
    num_players = num_cnts[0]
    num_clubs = num_cnts[1]
    num_league = num_cnts[2]
    num_country = num_cnts[3]

    player = [] # player[i] = 1 => i^th player is considered and 0 otherwise
    chem = []  # chem[i] = chemistry of i^th player

    # Preprocessing things to speed-up model creation time.
    # Thanks Gregory Wullimann !!
    players_grouped = {
        "Club": {}, "League": {}, "Country": {}, "Position": {},
        "Rating": {}, "Color": {}, "Rarity": {}, "Name": {}
    }
    for i in range(num_players):
        player.append(model.NewBoolVar(f"player{i}"))
        chem.append(model.NewIntVar(0, 3, f"chem{i}"))
        players_grouped["Club"][map_idx["Club"][df.at[i, "Club"]]] = players_grouped["Club"].get(map_idx["Club"][df.at[i, "Club"]], []) + [player[i]]
        players_grouped["League"][map_idx["League"][df.at[i,"League"]]] = players_grouped["League"].get(map_idx["League"][df.at[i,"League"]], []) + [player[i]]
        players_grouped["Country"][map_idx["Country"][df.at[i, "Country"]]] = players_grouped["Country"].get(map_idx["Country"][df.at[i, "Country"]], []) + [player[i]]
        players_grouped["Position"][map_idx["Position"][df.at[i, "Position"]]] = players_grouped["Position"].get(map_idx["Position"][df.at[i, "Position"]], []) + [player[i]]
        players_grouped["Rating"][map_idx["Rating"][df.at[i, "Rating"]]] = players_grouped["Rating"].get(map_idx["Rating"][df.at[i, "Rating"]], []) + [player[i]]
        players_grouped["Color"][map_idx["Color"][df.at[i, "Color"]]] = players_grouped["Color"].get(map_idx["Color"][df.at[i, "Color"]], []) + [player[i]]
        players_grouped["Rarity"][map_idx["Rarity"][df.at[i, "Rarity"]]] = players_grouped["Rarity"].get(map_idx["Rarity"][df.at[i, "Rarity"]], []) + [player[i]]
        players_grouped["Name"][map_idx["Name"][df.at[i, "Name"]]] = players_grouped["Name"].get(map_idx["Name"][df.at[i, "Name"]], []) + [player[i]]
  
    # These variables are basically chemistry of each club, league and nation
    z_club = [model.NewIntVar(0, 3, f"z_club{i}") for i in range(num_clubs)]
    z_league = [model.NewIntVar(0, 3, f"z_league{i}") for i in range(num_league)]
    z_nation = [model.NewIntVar(0, 3, f"z_nation{i}") for i in range(num_country)]

    # Needed for chemistry constraint
    b_c = [[model.NewBoolVar(f"b_c{j}{i}") for i in range(4)]for j in range(num_clubs)]
    b_l = [[model.NewBoolVar(f"b_l{j}{i}") for i in range(4)]for j in range(num_league)]
    b_n = [[model.NewBoolVar(f"b_n{j}{i}") for i in range(4)]for j in range(num_country)]

    # These variables represent whether a particular club, league or nation is
    # considered in the final solution or not
    club = [model.NewBoolVar(f"club_{i}") for i in range(num_clubs)]
    country = [model.NewBoolVar(f"country_{i}") for i in range(num_country)]
    league = [model.NewBoolVar(f"league_{i}") for i in range(num_league)]

    return model, player, chem, z_club, z_league, z_nation, b_c, b_l, b_n, club, country, league, players_grouped

@runtime
def create_basic_constraints(df, model, player, map_idx, players_grouped, num_cnts):
    '''Create some essential constraints'''
    num_players = num_cnts[0]

    # Max players in squad
    model.Add(cp_model.LinearExpr.Sum(player) == input.NUM_PLAYERS)

    # Unique players constraint. Currently different players of same name not present in dataset.
    # Same player with multiple card versions present.
    mark_name = {}
    for i in range(num_players):
        name = df.at[i, "Name"]
        if name in mark_name:
            continue
        mark_name[name] = 1
        expr = players_grouped["Name"].get(map_idx["Name"][name], [])
        model.Add(cp_model.LinearExpr.Sum(expr) <= 1)

    # Formation constraint
    if input.FIX_PLAYERS == 1:
        mark_pos = {}
        formation_list = input.formation_dict[input.FORMATION]
        for pos in formation_list:
            if pos in mark_pos:
                continue
            mark_pos[pos] = 1
            cnt = formation_list.count(pos)
            expr = players_grouped["Position"].get(map_idx["Position"][pos], [])
            model.Add(cp_model.LinearExpr.Sum(expr) == cnt)
    return model

@runtime
def create_country_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Create country constraint (>=)'''
    expr = []
    for nation in input.COUNTRY:
        expr += players_grouped["Country"].get(map_idx["Country"][nation], [])
    model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_COUNTRY)
    return model

@runtime
def create_league_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Create league constraint (>=)'''
    expr = []
    for league in input.LEAGUE:
        expr += players_grouped["League"].get(map_idx["League"][league], [])
    model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_LEAGUE)
    return model

@runtime
def create_club_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Create club constraint (>=)'''
    expr = []
    for club in input.CLUB:
        expr += players_grouped["Club"].get(map_idx["Club"][club], [])
    model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_CLUB)
    return model

@runtime
def create_rarity_1_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Create constraint for gold TOTW, gold Rare, gold Non Rare,
       silver TOTW, etc (>=).
    '''
    for i, rarity in enumerate(input.RARITY_1):
        idxes = list(df[(df["Color"] == rarity[0]) & (df["Rarity"] == rarity[1])].index)
        expr = [player[j] for j in idxes]
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_RARITY_1[i])
    return model

@runtime
def create_rarity_2_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''[Rare, Non Rare, TOTW, gold, silver, bronze ... etc] (>=).'''
    for i, rarity in enumerate(input.RARITY_2):
        col = "Rarity"
        if rarity in ["gold", "silver", "bronze"]:
            col = "Color"
        expr = players_grouped[col].get(map_idx[col][rarity], [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_RARITY_2[i])
    return model

@runtime
def create_squad_rating_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Squad Rating (>=)'''
    rating = df["Rating"].tolist()
    model.Add(cp_model.LinearExpr.WeightedSum(player, rating) >= (input.SQUAD_RATING) * (input.NUM_PLAYERS))
    return model

@runtime
def create_min_overall_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Minimum OVR of XX : Min X (>=)'''
    for i, rat in enumerate(input.MIN_OVERALL):
        expr = players_grouped["Rating"].get(map_idx["Rating"][rat], [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_MIN_OVERALL[i])
    return model

@runtime
def create_chemistry_constraint(df, model, chem, z_club, z_league, z_nation, player, players_grouped, num_cnts, map_idx, b_c, b_l, b_n):
    '''Optimize Chemistry (>=)
       Currently doesn't work for Icons and Heroes.
    '''
    num_players = num_cnts[0]
    num_clubs = num_cnts[1]
    num_league = num_cnts[2]
    num_country = num_cnts[3]

    club_dict, league_dict, country_dict = map_idx["Club"], map_idx["League"], map_idx["Country"]

    chem_expr = []
    for i in range(num_players):
        p_club, p_league, p_nation = df.at[i, "Club"], df.at[i, "League"], df.at[i, "Country"]
        sum_expr = z_club[club_dict[p_club]] + z_league[league_dict[p_league]] + z_nation[country_dict[p_nation]]
        b = model.NewBoolVar(f"b{i}")
        model.Add(sum_expr <= 3).OnlyEnforceIf(b)
        model.Add(sum_expr > 3).OnlyEnforceIf(b.Not())
        model.Add(chem[i] == sum_expr).OnlyEnforceIf(b)
        model.Add(chem[i] == 3).OnlyEnforceIf(b.Not())

        model.Add(chem[i] >= input.CHEM_PER_PLAYER).OnlyEnforceIf(player[i])

        player_chem_expr = model.NewIntVar(0, 3, f"chem_expr{i}")
        model.AddMultiplicationEquality(player_chem_expr, player[i], chem[i])
        chem_expr.append(player_chem_expr)

    club_bucket = [[0, 1], [2, 3], [4, 6], [7, input.NUM_PLAYERS]]

    for j in range(num_clubs):
        expr = players_grouped["Club"].get(j, [])
        sum_expr = cp_model.LinearExpr.Sum(expr)
        for idx, num in enumerate (club_bucket):
            lb, ub = club_bucket[idx][0], club_bucket[idx][1]
            model.AddLinearConstraint(sum_expr, lb, ub).OnlyEnforceIf(b_c[j][idx])
            model.Add(z_club[j] == idx).OnlyEnforceIf(b_c[j][idx])
        model.AddExactlyOne(b_c[j])

    league_bucket = [[0, 2], [3, 4], [5, 7], [8, input.NUM_PLAYERS]]

    for j in range(num_league):
        expr = players_grouped["League"].get(j, [])
        sum_expr = cp_model.LinearExpr.Sum(expr)
        for idx, num in enumerate (league_bucket):
            lb, ub = league_bucket[idx][0], league_bucket[idx][1]
            model.AddLinearConstraint(sum_expr, lb, ub).OnlyEnforceIf(b_l[j][idx])
            model.Add(z_league[j] == idx).OnlyEnforceIf(b_l[j][idx])
        model.AddExactlyOne(b_l[j])

    country_bucket = [[0, 1], [2, 4], [5, 7], [8, input.NUM_PLAYERS]]

    for j in range(num_country):
        expr = players_grouped["Country"].get(j, [])
        sum_expr = cp_model.LinearExpr.Sum(expr)
        for idx, num in enumerate(country_bucket):
            lb, ub = country_bucket[idx][0], country_bucket[idx][1]
            model.AddLinearConstraint(sum_expr, lb, ub).OnlyEnforceIf(b_n[j][idx])
            model.Add(z_nation[j] == idx).OnlyEnforceIf(b_n[j][idx])
        model.AddExactlyOne(b_n[j])

    model.Add(cp_model.LinearExpr.Sum(chem_expr) >= input.CHEMISTRY)
    return model

@runtime
def create_max_club_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Maximum player from same club (<=)'''
    num_clubs = num_cnts[1]
    for i in range(num_clubs):
        expr = players_grouped["Club"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) <= input.MAX_NUM_CLUB)
    return model

@runtime
def create_max_league_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Maximum player from same league (<=)'''
    num_league = num_cnts[2]
    for i in range(num_league):
        expr = players_grouped["League"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) <= input.MAX_NUM_LEAGUE)
    return model

@runtime
def create_max_country_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Maximum player from same country (<=)'''
    num_country = num_cnts[3]
    for i in range(num_country):
        expr = players_grouped["Country"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) <= input.MAX_NUM_COUNTRY)
    return model

@runtime
def create_min_club_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Same Club Count: Min X (>=)'''
    num_clubs = num_cnts[1]
    B_C = [model.NewBoolVar(f"B_C{i}") for i in range(num_clubs)]
    for i in range(num_clubs):
        expr = players_grouped["Club"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.MIN_NUM_CLUB).OnlyEnforceIf(B_C[i])
        model.Add(cp_model.LinearExpr.Sum(expr) < input.MIN_NUM_CLUB).OnlyEnforceIf(B_C[i].Not())
    model.AddAtLeastOne(B_C)
    return model

@runtime
def create_min_league_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Same League Count: Min X (>=)'''
    num_league = num_cnts[2]
    B_L = [model.NewBoolVar(f"B_L{i}") for i in range(num_league)]
    for i in range(num_league):
        expr = players_grouped["League"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.MIN_NUM_LEAGUE).OnlyEnforceIf(B_L[i])
        model.Add(cp_model.LinearExpr.Sum(expr) < input.MIN_NUM_LEAGUE).OnlyEnforceIf(B_L[i].Not())
    model.AddAtLeastOne(B_L)
    return model

@runtime
def create_min_country_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Same Nation Count: Min X (>=)'''
    num_country = num_cnts[3]
    B_N = [model.NewBoolVar(f"B_N{i}") for i in range(num_country)]
    for i in range(num_country):
        expr = players_grouped["Country"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.MIN_NUM_COUNTRY).OnlyEnforceIf(B_N[i])
        model.Add(cp_model.LinearExpr.Sum(expr) < input.MIN_NUM_COUNTRY).OnlyEnforceIf(B_N[i].Not())
    model.AddAtLeastOne(B_N)
    return model

@runtime
def create_unique_club_constraint(df, model, player, club, map_idx, players_grouped, num_cnts):
    '''Clubs: Max/Min X'''
    num_clubs = num_cnts[1]
    for i in range(num_clubs):
        expr = players_grouped["Club"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= 1).OnlyEnforceIf(club[i])
        model.Add(cp_model.LinearExpr.Sum(expr) == 0).OnlyEnforceIf(club[i].Not())
    model.Add(cp_model.LinearExpr.Sum(club) >= input.NUM_UNIQUE_CLUB)
    return model

@runtime
def create_unique_league_constraint(df, model, player, league, map_idx, players_grouped, num_cnts):
    '''Leagues: Max/Min X'''
    num_league = num_cnts[2]
    for i in range(num_league):
        expr = players_grouped["League"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= 1).OnlyEnforceIf(league[i])
        model.Add(cp_model.LinearExpr.Sum(expr) == 0).OnlyEnforceIf(league[i].Not())
    model.Add(cp_model.LinearExpr.Sum(league) >= input.NUM_UNIQUE_LEAGUE)
    return model

@runtime
def create_unique_country_constraint(df, model, player, country, map_idx, players_grouped, num_cnts):
    '''Nations: Max/Min X'''
    num_country = num_cnts[3]
    for i in range(num_country):
        expr = players_grouped["Country"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= 1).OnlyEnforceIf(country[i])
        model.Add(cp_model.LinearExpr.Sum(expr) == 0).OnlyEnforceIf(country[i].Not())
    model.Add(cp_model.LinearExpr.Sum(country) >= input.NUM_UNIQUE_COUNTRY)
    return model

def set_objective(df, model, player):
    '''Set objective (minimize) based on cost'''
    cost = df["Cost"].tolist()
    model.Minimize(cp_model.LinearExpr.WeightedSum(player, cost))
    return model

def get_dict(df, col):
   '''Map fields to a unique index'''
   d = {}
   unique_col = df[col].unique()
   for i, val in enumerate(unique_col):
    d[val] = i
   return d

@runtime
def SBC(df):
    '''Optimize SBC using Constraint Integer Programming'''
    num_cnts = [df.shape[0], df.Club.nunique(), df.League.nunique(), df.Country.nunique()] # Count of important fields

    map_idx= {} # Map fields to a unique index
    fields = ["Club", "League", "Country", "Position", "Rating", "Color", "Rarity", "Name"]
    for field in fields:
        map_idx[field] = get_dict(df, field)

    '''Create the CP-SAT Model'''
    model = cp_model.CpModel()

    '''Create essential variables and do some pre-processing'''
    model, player, chem, z_club, z_league, z_nation, b_c, b_l, b_n, club, country, league, players_grouped = create_var(model, df, map_idx, num_cnts)

    '''Essential constraints'''
    model = create_basic_constraints(df, model, player, map_idx, players_grouped, num_cnts)

    '''Comment out the constraints not required'''
    # model = create_club_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_league_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_country_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_squad_rating_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_min_overall_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    model = create_max_club_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_max_league_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_max_country_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_unique_club_constraint(df, model, player, club, map_idx, players_grouped, num_cnts)
    model = create_unique_league_constraint(df, model, player, league, map_idx, players_grouped, num_cnts)
    # model = create_unique_country_constraint(df, model, player, country, map_idx, players_grouped, num_cnts)
    # model = create_min_club_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_min_league_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    model = create_min_country_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_rarity_1_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    model = create_rarity_2_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    '''Comment out the constraints not required'''

    '''
       If there is no constraint on total chemistry, simply set input.CHEMISTRY = 0
       instead of commenting out this constraint.
    '''
    model = create_chemistry_constraint(df, model, chem, z_club, z_league, z_nation, player, players_grouped, num_cnts, map_idx, b_c, b_l, b_n)

    '''Set objective based on player cost'''
    model = set_objective(df, model, player)

    '''Export Model to file'''
    # model.ExportToFile('model.txt')

    '''Solve'''
    print("Solve Started")
    solver = cp_model.CpSolver()

    '''Solver Parameters'''
    # solver.parameters.random_seed = 42
    solver.parameters.max_time_in_seconds = 50000
    # solver.parameters.log_search_progress = True
    # Specify the number of parallel workers (i.e. threads) to use during search (default = 8).
    # This should usually be lower than your number of available cpus + hyperthread in your machine.
    # Set to 16 or 24 if you have high-end CPU :).
    solver.parameters.num_search_workers = 8
    # solver.parameters.cp_model_presolve = False
    # solver.parameters.stop_after_first_solution = True
    '''Solver Parameters'''

    status = solver.Solve(model)
    print(input.status_dict[status])
    print('\n')
    final_players = []
    if status == 2 or status == 4: # Feasible or Optimal   
        df['Chemistry'] = 0 # We only care about chemistry of selected players
        for i in range(num_cnts[0]):
            if solver.Value(player[i]) == 1:
                final_players.append(i)
                df.loc[i, "Chemistry"] = solver.Value(chem[i])
    return final_players

