import input
from threading import Timer
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

class ObjectiveEarlyStopping(cp_model.CpSolverSolutionCallback):
    '''Stop the search if the objective remains the same for X seconds'''
    def __init__(self, timer_limit: int):
        super().__init__()
        self._timer_limit = timer_limit
        self._timer = None

    def on_solution_callback(self):
        '''This is called everytime a solution with better objective is found.'''
        self._reset_timer()

    def _reset_timer(self):
        if self._timer:
            self._timer.cancel()
        self._timer = Timer(self._timer_limit, self.StopSearch)
        self._timer.start()

    def StopSearch(self):
        print(f"{self._timer_limit} seconds without improvement in objective. ")
        super().StopSearch()

@runtime
def create_var(model, df, map_idx, num_cnts):
    '''Create the relevant variables'''
    num_players, num_clubs, num_league, num_country = num_cnts[0], num_cnts[1], num_cnts[2], num_cnts[3]

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
    # Max players in squad
    model.Add(cp_model.LinearExpr.Sum(player) == input.NUM_PLAYERS)

    # Unique players constraint. Currently different players of same name not present in dataset.
    # Same player with multiple card versions present.
    for idx, expr in players_grouped["Name"].items():
        model.Add(cp_model.LinearExpr.Sum(expr) <= 1)

    # Formation constraint
    if input.PLAYERS_IN_POSITION == True:
        formation_list = input.formation_dict[input.FORMATION]
        cnt = {}
        for pos in formation_list:
            cnt[pos] = formation_list.count(pos)
        for pos, num in cnt.items():
            expr = players_grouped["Position"].get(map_idx["Position"][pos], [])
            model.Add(cp_model.LinearExpr.Sum(expr) == num)
    return model

@runtime
def create_country_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Create country constraint (>=)'''
    for i, nation_list in enumerate(input.COUNTRY):
        expr = []
        for nation in nation_list:
            expr += players_grouped["Country"].get(map_idx["Country"][nation], [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_COUNTRY[i])
    return model

@runtime
def create_league_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Create league constraint (>=)'''
    for i, league_list in enumerate(input.LEAGUE):
        expr = []
        for league in league_list:
            expr += players_grouped["League"].get(map_idx["League"][league], [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_LEAGUE[i])
    return model

@runtime
def create_club_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Create club constraint (>=)'''
    for i, club_list in enumerate(input.CLUB):
        expr = []
        for club in club_list:
            expr += players_grouped["Club"].get(map_idx["Club"][club], [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_CLUB[i])
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
    '''[Rare, Common, TOTW, Gold, Silver, Bronze ... etc] (>=).'''
    for i, rarity_type in enumerate(input.RARITY_2):
        expr = []
        if rarity_type in ["Gold", "Silver", "Bronze"]:
            expr = players_grouped["Color"].get(map_idx["Color"].get(rarity_type, -1), [])
        elif rarity_type == "Rare":
            # Consider the following cards as Rare.
            for rarity in input.CONSIDER_AS_RARE:
                expr += players_grouped["Rarity"].get(map_idx["Rarity"].get(rarity, -1), [])
        elif rarity_type == "Common":
            # Consider everthing other than the above as Common.
            common_rarities = list(set(df["Rarity"].unique().tolist()) - set(input.CONSIDER_AS_RARE))
            for rarity in common_rarities:
                expr += players_grouped["Rarity"].get(map_idx["Rarity"].get(rarity, -1), [])
        else:
            expr = players_grouped["Rarity"].get(map_idx["Rarity"].get(rarity_type, -1), [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_RARITY_2[i])
    return model

@runtime
def create_squad_rating_constraint_1(df, model, player, map_idx, players_grouped, num_cnts):
    '''Squad Rating: Min XX (>=) based on average rating.'''
    rating = df["Rating"].tolist()
    model.Add(cp_model.LinearExpr.WeightedSum(player, rating) >= (input.SQUAD_RATING) * (input.NUM_PLAYERS))
    return model

@runtime
def create_squad_rating_constraint_2(df, model, player, map_idx, players_grouped, num_cnts):
    '''Squad Rating: Min XX (>=) based on
    https://www.reddit.com/r/EASportsFC/comments/5osq7k/new_overall_rating_figured_out.
    Probably more accurate.
    '''
    num_players = num_cnts[0]
    rating = df["Rating"].tolist()
    avg_rat = cp_model.LinearExpr.WeightedSum(player, rating) # Assuming that the original ratings have been scaled by 11 (input.NUM_PLAYERS).
    # This represents the max non-negative gap between player rating and squad avg_rating.
    # Should be set to a reasonable amount to avoid overwhelming the solver.
    # Good solutions likely don't have large gap anyways.
    max_gap_bw_rating = min(150, (df["Rating"].max() - df["Rating"].min()) * (input.NUM_PLAYERS - 1)) # max_rat * 11 - (min_rat * 10 + max_rat) (seems alright).
    excess = [model.NewIntVar(0, max_gap_bw_rating, f"excess{i}") for i in range(num_players)]
    [model.AddMaxEquality(excess[i], [(player[i] * rat * input.NUM_PLAYERS - avg_rat), 0])  for i, rat in enumerate(rating)]
    sum_excess = cp_model.LinearExpr.Sum(excess)
    model.Add((avg_rat * input.NUM_PLAYERS + sum_excess) >= (input.SQUAD_RATING) * (input.NUM_PLAYERS) * (input.NUM_PLAYERS))
    return model

@runtime
def create_squad_rating_constraint_3(df, model, player, map_idx, players_grouped, num_cnts):
    '''Squad Rating: Min XX (>=).
    Another way to model 'create_squad_rating_constraint_2'.
    This significantly speeds up the model creation time and for some reason
    the solver converges noticeably faster to a good solution, even without a rating filter
    when tested on a single constraint like Squad Rating: Min XX.
    '''
    rat_list = df["Rating"].unique().tolist()
    R = {} # This variable represents how many players have a particular rating in the final solution.
    rat_expr = []
    for rat in (rat_list):
        rat_idx = map_idx["Rating"][rat]
        expr = players_grouped["Rating"].get(rat_idx, [])
        R[rat_idx] = model.NewIntVar(0, input.NUM_PLAYERS, f"R{rat_idx}")
        rat_expr.append(R[rat_idx] * rat)
        model.Add(R[rat_idx] == cp_model.LinearExpr.Sum(expr))
    avg_rat = cp_model.LinearExpr.Sum(rat_expr)
    # This is similar in concept to the excess variable in create_squad_rating_constraint_2.
    excess = [model.NewIntVar(0, 1500, f"excess{i}") for i in range(len(rat_list))]
    for rat in (rat_list):
        rat_idx = map_idx["Rating"][rat]
        lhs = rat * input.NUM_PLAYERS * R[rat_idx]
        rat_expr_1 = []
        for rat_1 in (rat_list):
            rat_idx_1 = map_idx["Rating"][rat_1]
            temp = model.NewIntVar(0, 15000, f"temp{rat_idx_1}")
            model.AddMultiplicationEquality(temp, R[rat_idx], R[rat_idx_1] * rat_1)
            rat_expr_1.append(temp)
        rhs = cp_model.LinearExpr.Sum(rat_expr_1)
        model.AddMaxEquality(excess[rat_idx], [lhs - rhs, 0])
    sum_excess = cp_model.LinearExpr.Sum(excess)
    model.Add((avg_rat * input.NUM_PLAYERS + sum_excess) >= (input.SQUAD_RATING) * (input.NUM_PLAYERS) * (input.NUM_PLAYERS))
    return model

@runtime
def create_min_overall_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Minimum OVR of XX : Min X (>=)'''
    MAX_RATING = df["Rating"].max()
    for i, rating in enumerate(input.MIN_OVERALL):
        expr = []
        for rat in range(rating, MAX_RATING + 1):
            if rat not in map_idx["Rating"]:
                continue
            expr += players_grouped["Rating"].get(map_idx["Rating"][rat], [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= input.NUM_MIN_OVERALL[i])
    return model

@runtime
def create_chemistry_constraint(df, model, chem, z_club, z_league, z_nation, player, players_grouped, num_cnts, map_idx, b_c, b_l, b_n):
    '''Optimize Chemistry (>=)
    (https://www.rockpapershotgun.com/fifa-23-chemistry)
    '''
    num_players, num_clubs, num_league, num_country = num_cnts[0], num_cnts[1], num_cnts[2], num_cnts[3]

    club_dict, league_dict, country_dict, pos_dict = map_idx["Club"], map_idx["League"], map_idx["Country"], map_idx["Position"]

    formation_list = input.formation_dict[input.FORMATION]

    pos = [] # pos[i] = 1 => player[i] should be placed in their position.
    m_pos, m_idx = {}, {}
    chem_expr = []

    for i in range(num_players):
        p_club, p_league, p_nation, p_pos = df.at[i, "Club"], df.at[i, "League"], df.at[i, "Country"], df.at[i, "Position"]
        pos.append(model.NewBoolVar(f"_pos{i}"))
        m_pos[player[i]] = pos[i]
        m_idx[player[i]] = i
        if p_pos in formation_list:
            if input.PLAYERS_IN_POSITION == True:
                model.Add(pos[i] == 1)
            if df.at[i, "Rarity"] in ["Icon", "UT Heroes"]:
                model.Add(chem[i] == 3)
            elif df.at[i, "Rarity"] in ["Radioactive", "FC Versus Ice", "FC Versus Fire"]:
                model.Add(chem[i] == 2)
            else:
                sum_expr = z_club[club_dict[p_club]] + z_league[league_dict[p_league]] + z_nation[country_dict[p_nation]]
                b = model.NewBoolVar(f"b{i}")
                model.Add(sum_expr <= 3).OnlyEnforceIf(b)
                model.Add(sum_expr > 3).OnlyEnforceIf(b.Not())
                model.Add(chem[i] == sum_expr).OnlyEnforceIf(b)
                model.Add(chem[i] == 3).OnlyEnforceIf(b.Not())
        else:
            model.Add(chem[i] == 0)
            model.Add(pos[i] == 0)

        model.Add(chem[i] >= input.CHEM_PER_PLAYER).OnlyEnforceIf(player[i])
        play_pos = model.NewBoolVar(f"play_pos{i}")
        model.AddMultiplicationEquality(play_pos, player[i], pos[i])
        player_chem_expr = model.NewIntVar(0, 3, f"chem_expr{i}")
        model.AddMultiplicationEquality(player_chem_expr, play_pos, chem[i])
        chem_expr.append(player_chem_expr)

    pos_expr = [] # Players whose position is there in the input formation.

    '''
        For example say if the solver selects 3 CMs in the final
        solution but we only need at-most 2 of them to be in position for a 3-4-3
        formation and be considered for chemistry calcuation.
    '''
    for Pos in set(formation_list):
        if Pos not in pos_dict:
                continue
        t_expr = players_grouped["Position"].get(pos_dict[Pos], [])
        pos_expr += t_expr
        if input.PLAYERS_IN_POSITION == False:
            play_pos = [model.NewBoolVar(f"play_pos{Pos}{i}") for i in range(len(t_expr))]
            [model.AddMultiplicationEquality(play_pos[i], p, m_pos[p]) for i, p in enumerate(t_expr)]
            model.Add(cp_model.LinearExpr.Sum(play_pos) <= formation_list.count(Pos))

    club_bucket = [[0, 1], [2, 3], [4, 6], [7, input.NUM_PLAYERS]]

    for j in range(num_clubs):
        t_expr = players_grouped["Club"].get(j, [])
        # We need players from j^th club whose position is there in the input formation.
        # Since only such players would contribute towards chemistry.
        t_expr_1 = list(set(t_expr) & set(pos_expr))
        expr = []
        for i, p in enumerate(t_expr_1):
            if df.at[m_idx[p], "Rarity"] in ["Icon", "UT Heroes"]: # Heroes or Icons don't contribute to club chem.
                continue
            t_var = model.NewBoolVar(f"t_var_c{i}")
            model.AddMultiplicationEquality(t_var, p, m_pos[p])
            if df.at[m_idx[p], "Rarity"] == "Radioactive": # Radioactive cards contribute 2x to club chem.
                expr.append(2 * t_var)
            elif df.at[m_idx[p], "Rarity"] == "FC Versus Ice": # Ice cards contribute 5x to club chem.
                expr.append(5 * t_var)
            else:
                expr.append(t_var)
        sum_expr = cp_model.LinearExpr.Sum(expr)
        for idx in range(4):
            lb, ub = club_bucket[idx][0], club_bucket[idx][1]
            model.AddLinearConstraint(sum_expr, lb, ub).OnlyEnforceIf(b_c[j][idx])
            model.Add(z_club[j] == idx).OnlyEnforceIf(b_c[j][idx])
        model.AddExactlyOne(b_c[j])

    league_bucket = [[0, 2], [3, 4], [5, 7], [8, input.NUM_PLAYERS]]

    icons_expr = players_grouped["Rarity"].get(map_idx["Rarity"].get("Icon", -1), [])

    for j in range(num_league):
        t_expr = players_grouped["League"].get(j, [])
        t_expr += icons_expr # In EA FC 24, Icons add 1 chem to every league in the squad.
        # We need players from j^th league whose position is there in the input formation.
        # Since only such players would contribute towards chemistry.
        t_expr_1 = list(set(t_expr) & set(pos_expr))
        expr = []
        for i, p in enumerate(t_expr_1):
            t_var = model.NewBoolVar(f"t_var_l{i}")
            model.AddMultiplicationEquality(t_var, p, m_pos[p])
            if df.at[m_idx[p], "Rarity"] in ["UT Heroes", "Radioactive"]:  # Heroes / Radioactive cards contribute 2x to league chem.
                expr.append(2 * t_var)
            else:
                expr.append(t_var)
        sum_expr = cp_model.LinearExpr.Sum(expr)
        for idx in range(4):
            lb, ub = league_bucket[idx][0], league_bucket[idx][1]
            model.AddLinearConstraint(sum_expr, lb, ub).OnlyEnforceIf(b_l[j][idx])
            model.Add(z_league[j] == idx).OnlyEnforceIf(b_l[j][idx])
        model.AddExactlyOne(b_l[j])

    country_bucket = [[0, 1], [2, 4], [5, 7], [8, input.NUM_PLAYERS]]

    for j in range(num_country):
        t_expr = players_grouped["Country"].get(j, [])
        # We need players from j^th country whose position is there in the input formation.
        # Since only such players would contribute towards chemistry.
        t_expr_1 = list(set(t_expr) & set(pos_expr))
        expr = []
        for i, p in enumerate(t_expr_1):
            t_var = model.NewBoolVar(f"t_var_n{i}")
            model.AddMultiplicationEquality(t_var, p, m_pos[p])
            if df.at[m_idx[p], "Rarity"] in ["Icon", "Radioactive"]:  # Icons / Radioactive cards contribute 2x to country chem.
                expr.append(2 * t_var)
            elif df.at[m_idx[p], "Rarity"] == "FC Versus Fire": # Fire cards contribute 5x to country chem.
                expr.append(5 * t_var)
            else:
                expr.append(t_var)
        sum_expr = cp_model.LinearExpr.Sum(expr)
        for idx in range(4):
            lb, ub = country_bucket[idx][0], country_bucket[idx][1]
            model.AddLinearConstraint(sum_expr, lb, ub).OnlyEnforceIf(b_n[j][idx])
            model.Add(z_nation[j] == idx).OnlyEnforceIf(b_n[j][idx])
        model.AddExactlyOne(b_n[j])

    model.Add(cp_model.LinearExpr.Sum(chem_expr) >= input.CHEMISTRY)
    return model, pos, chem_expr

@runtime
def create_max_club_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Same Club Count: Max X / Max X Players from the Same Club (<=)'''
    num_clubs = num_cnts[1]
    for i in range(num_clubs):
        expr = players_grouped["Club"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) <= input.MAX_NUM_CLUB)
    return model

@runtime
def create_max_league_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Same League Count: Max X / Max X Players from the Same League (<=)'''
    num_league = num_cnts[2]
    for i in range(num_league):
        expr = players_grouped["League"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) <= input.MAX_NUM_LEAGUE)
    return model

@runtime
def create_max_country_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Same Nation Count: Max X / Max X Players from the Same Nation (<=)'''
    num_country = num_cnts[3]
    for i in range(num_country):
        expr = players_grouped["Country"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) <= input.MAX_NUM_COUNTRY)
    return model

@runtime
def create_min_club_constraint(df, model, player, map_idx, players_grouped, num_cnts):
    '''Same Club Count: Min X / Min X Players from the Same Club (>=)'''
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
    '''Same League Count: Min X / Min X Players from the Same League (>=)'''
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
    '''Same Nation Count: Min X / Min X Players from the Same Nation (>=)'''
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
    '''Clubs: Max / Min / Exactly X'''
    num_clubs = num_cnts[1]
    for i in range(num_clubs):
        expr = players_grouped["Club"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= 1).OnlyEnforceIf(club[i])
        model.Add(cp_model.LinearExpr.Sum(expr) == 0).OnlyEnforceIf(club[i].Not())
    if input.NUM_UNIQUE_CLUB[1] == "Min":
        model.Add(cp_model.LinearExpr.Sum(club) >= input.NUM_UNIQUE_CLUB[0])
    elif input.NUM_UNIQUE_CLUB[1] == "Max":
        model.Add(cp_model.LinearExpr.Sum(club) <= input.NUM_UNIQUE_CLUB[0])
    elif input.NUM_UNIQUE_CLUB[1] == "Exactly":
        model.Add(cp_model.LinearExpr.Sum(club) == input.NUM_UNIQUE_CLUB[0])
    else:
        print("**Couldn't create unique_club_constraint!**")
    return model

@runtime
def create_unique_league_constraint(df, model, player, league, map_idx, players_grouped, num_cnts):
    '''Leagues: Max / Min / Exactly X'''
    num_league = num_cnts[2]
    for i in range(num_league):
        expr = players_grouped["League"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= 1).OnlyEnforceIf(league[i])
        model.Add(cp_model.LinearExpr.Sum(expr) == 0).OnlyEnforceIf(league[i].Not())
    if input.NUM_UNIQUE_LEAGUE[1] == "Min":
        model.Add(cp_model.LinearExpr.Sum(league) >= input.NUM_UNIQUE_LEAGUE[0])
    elif input.NUM_UNIQUE_LEAGUE[1] == "Max":
        model.Add(cp_model.LinearExpr.Sum(league) <= input.NUM_UNIQUE_LEAGUE[0])
    elif input.NUM_UNIQUE_LEAGUE[1] == "Exactly":
        model.Add(cp_model.LinearExpr.Sum(league) == input.NUM_UNIQUE_LEAGUE[0])
    else:
        print("**Couldn't create unique_league_constraint!**")
    return model

@runtime
def create_unique_country_constraint(df, model, player, country, map_idx, players_grouped, num_cnts):
    '''Nations: Max / Min / Exactly X'''
    num_country = num_cnts[3]
    for i in range(num_country):
        expr = players_grouped["Country"].get(i, [])
        model.Add(cp_model.LinearExpr.Sum(expr) >= 1).OnlyEnforceIf(country[i])
        model.Add(cp_model.LinearExpr.Sum(expr) == 0).OnlyEnforceIf(country[i].Not())
    if input.NUM_UNIQUE_COUNTRY[1] == "Min":
        model.Add(cp_model.LinearExpr.Sum(country) >= input.NUM_UNIQUE_COUNTRY[0])
    elif input.NUM_UNIQUE_COUNTRY[1] == "Max":
        model.Add(cp_model.LinearExpr.Sum(country) <= input.NUM_UNIQUE_COUNTRY[0])
    elif input.NUM_UNIQUE_COUNTRY[1] == "Exactly":
        model.Add(cp_model.LinearExpr.Sum(country) == input.NUM_UNIQUE_COUNTRY[0])
    else:
        print("**Couldn't create unique_country_constraint!**")
    return model

@runtime
def prioritize_duplicates(df, model, player):
    dup_idxes = list(df[(df["IsDuplicate"] == True)].index)
    if not dup_idxes:
        print("**No Duplicates Found!**")
        return model
    duplicates = [player[j] for j in dup_idxes]
    dup_expr = cp_model.LinearExpr.Sum(duplicates)
    if input.USE_ALL_DUPLICATES:
        model.Add(dup_expr == min(input.NUM_PLAYERS, len(dup_idxes)))
    elif input.USE_AT_LEAST_HALF_DUPLICATES:
        model.Add(2 * dup_expr >= min(input.NUM_PLAYERS, len(dup_idxes)))
    elif input.USE_AT_LEAST_ONE_DUPLICATE:
        model.Add(dup_expr >= 1)
    return model

@runtime
def fix_players(df, model, player):
    '''Fix specific players and optimize the rest'''
    if not input.FIX_PLAYERS:
        return model
    missing_players = []
    for idx in input.FIX_PLAYERS:
        idxes = list(df[(df["Original_Idx"] == (idx - 2))].index)
        if not idxes:
            missing_players.append(idx)
            continue
        players_to_fix = [player[j] for j in idxes]
        # Note: A selected player may play in multiple positions.
        # Any one such version must be fixed.
        model.Add(cp_model.LinearExpr.Sum(players_to_fix) == 1)
    if missing_players:
        print(f"**Couldn't fix the following players with Row_ID: {missing_players}**")
        print(f"**They may have already been filtered out**")
    return model

@runtime
def set_objective(df, model, player):
    '''Set objective based on player cost.
    The default behaviour of the solver is to minimize the overall cost.
    '''
    cost = df["Cost"].tolist()
    if input.MINIMIZE_MAX_COST:
        print("**MINIMIZE_MAX_COST**")
        max_cost = model.NewIntVar(0, df["Cost"].max(), "max_cost")
        play_cost = [player[i] * cost[i] for i in range(len(cost))]
        model.AddMaxEquality(max_cost, play_cost)
        model.Minimize(max_cost)
    elif input.MAXIMIZE_TOTAL_COST:
        print("**MAXIMIZE_TOTAL_COST**")
        model.Maximize(cp_model.LinearExpr.WeightedSum(player, cost))
    else:
        print("**MINIMIZE_TOTAL_COST**")
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

    '''Club'''
    # model = create_club_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    model = create_max_club_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_min_club_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_unique_club_constraint(df, model, player, club, map_idx, players_grouped, num_cnts)
    '''Club'''

    '''League'''
    # model = create_league_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_max_league_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_min_league_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    model = create_unique_league_constraint(df, model, player, league, map_idx, players_grouped, num_cnts)
    '''League'''

    '''Country'''
    # model = create_country_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_max_country_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    # model = create_min_country_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    model = create_unique_country_constraint(df, model, player, country, map_idx, players_grouped, num_cnts)
    '''Country'''

    '''Rarity'''
    # model = create_rarity_1_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    model = create_rarity_2_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    '''Rarity'''

    '''Squad Rating'''
    model = create_squad_rating_constraint_3(df, model, player, map_idx, players_grouped, num_cnts)
    '''Squad Rating'''

    '''Min Overall'''
    # model = create_min_overall_constraint(df, model, player, map_idx, players_grouped, num_cnts)
    '''Min Overall'''

    '''Duplicates'''
    # model = prioritize_duplicates(df, model, player)

    '''Comment out the constraints not required'''

    '''If there is no constraint on total chemistry, simply set input.CHEMISTRY = 0'''
    model, pos, chem_expr = create_chemistry_constraint(df, model, chem, z_club, z_league, z_nation, player, players_grouped, num_cnts, map_idx, b_c, b_l, b_n)

    '''Fix specific players and optimize the rest'''
    model = fix_players(df, model, player)

    '''Set objective based on player cost'''
    model = set_objective(df, model, player)

    '''Export Model to file'''
    # model.ExportToFile('model.txt')

    '''Solve'''
    print("Solve Started")
    solver = cp_model.CpSolver()

    '''Solver Parameters'''
    # solver.parameters.random_seed = 42
    solver.parameters.max_time_in_seconds = 600
    # Whether the solver should log the search progress.
    solver.parameters.log_search_progress = True
    # Specify the number of parallel workers (i.e. threads) to use during search.
    # This should usually be lower than your number of available cpus + hyperthread in your machine.
    # Setting this to 16 or 24 can help if the solver is slow in improving the bound.
    solver.parameters.num_search_workers = 16
    # Stop the search when the gap between the best feasible objective (O) and
    # our best objective bound (B) is smaller than a limit.
    # Relative: abs(O - B) / max(1, abs(O)).
    # Note that if the gap is reached, the search status will be OPTIMAL. But
    # one can check the best objective bound to see the actual gap.
    # solver.parameters.relative_gap_limit = 0.05
    # solver.parameters.cp_model_presolve = False
    # solver.parameters.stop_after_first_solution = True
    '''Solver Parameters'''

    status = solver.Solve(model, ObjectiveEarlyStopping(timer_limit = 60))
    print(input.status_dict[status])
    print('\n')
    final_players = []
    if status == 2 or status == 4: # Feasible or Optimal
        df['Chemistry'] = 0
        df['Is_Pos'] = 0 # Is_Pos = 1 => Player should be placed in their respective position.
        for i in range(num_cnts[0]):
            if solver.Value(player[i]) == 1:
                final_players.append(i)
                df.loc[i, "Chemistry"] = solver.Value(chem_expr[i])
                df.loc[i, "Is_Pos"] = solver.Value(pos[i])
    return final_players
