'''INPUTS'''

FORMATION = "4-4-2"

NUM_PLAYERS = 11

PLAYERS_IN_POSITION = False # PLAYERS_IN_POSITION = True => No player will be out of position and False implies otherwise.

# This can be used to fix specific players and optimize the rest.
# Find the Row_ID (starts from 2) of each player to be fixed
# from the club dataset and plug that in.
FIX_PLAYERS = []

# Filter out specific players using Row_ID.
REMOVE_PLAYERS = []

# Change the nature of the objective.
# By default, the solver tries to minimize the overall cost.
# Set only one of the below to True to change the objective type.
MINIMIZE_MAX_COST = False # This minimizes the max cost within a solution. This is worth a try but not that effective.
MAXIMIZE_TOTAL_COST = False # Could be used for building a good team.

# Set only one of the below to True and the other to False. Both can't be False.
USE_PREFERRED_POSITION = False
USE_ALTERNATE_POSITIONS = True

# Set only one of the below to True and the others to False if duplicates are to be prioritized.
USE_ALL_DUPLICATES = False
USE_AT_LEAST_HALF_DUPLICATES = False
USE_AT_LEAST_ONE_DUPLICATE = False

# Which cards should be considered Rare or Common?
# Source: https://www.fut.gg/rarities/
# Source: https://www.ea.com/en-gb/games/fifa/fifa-23/news/explaining-rarity-in-fifa-ultimate-team
# Source: https://www.reddit.com/r/EASportsFC/comments/pajy29/how_do_ea_determine_wether_a_card_is_rare_or_none/
# Source: https://www.reddit.com/r/EASportsFC/comments/16qfz75/psa_libertadores_cards_no_longer_count_as_rares/
# Note: Apparently, EA randomly assigns a card as Rare. I kind of forgot to factor in this fact.
# Note: In v1.1.0.3 of the extension, the actual rarity of each card is now displayed in the club dataset.
# Note: Everything else is considered as a Common card. Keep modifying this as it is incomplete and could also be wrong!
CONSIDER_AS_RARE = ["Rare", "TOTW", "Icon", "UT Heroes", "Nike", "UCL Road to the Knockouts",
                    "UEL Road to the Knockouts", "UWCL Road to the Knockouts", "UECL Road to the Knockouts"]

CLUB = [["Real Madrid", "Arsenal"], ["FC Bayern"]]
NUM_CLUB = [3, 2]  # Total players from i^th list >= NUM_CLUB[i]

MAX_NUM_CLUB = 5  # Same Club Count: Max X / Max X Players from the Same Club
MIN_NUM_CLUB = 2  # Same Club Count: Min X / Min X Players from the Same Club
NUM_UNIQUE_CLUB = [5, "Max"]  # Clubs: Max / Min / Exactly X

LEAGUE = [["Premier League", "LaLiga Santander"]]
NUM_LEAGUE = [11]  # Total players from i^th list >= NUM_LEAGUE[i]

MAX_NUM_LEAGUE = 4  # Same League Count: Max X / Max X Players from the Same League
MIN_NUM_LEAGUE = 4  # Same League Count: Min X / Min X Players from the Same League
NUM_UNIQUE_LEAGUE = [5, "Min"]  # Leagues: Max / Min / Exactly X

COUNTRY = [["England", "Spain"], ["Germany"]]
NUM_COUNTRY = [2, 1] # Total players from i^th list >= NUM_COUNTRY[i]

MAX_NUM_COUNTRY = 3  # Same Nation Count: Max X / Max X Players from the Same Nation
MIN_NUM_COUNTRY = 5  # Same Nation Count: Min X / Min X Players from the Same Nation
NUM_UNIQUE_COUNTRY = [5, "Min"]  # Nations: Max / Min / Exactly X

RARITY_1 = [['Gold', 'TOTW']]
NUM_RARITY_1 = [1]  # This is for cases like "Gold TOTW: Min X (0/X)"

# [Rare, Common, TOTW, Gold, Silver, Bronze ... etc]
# Note: Unfortunately several cards like 'TOTW' are listed as 'Special'
# Note: This is fixed in v1.1.0.3 of the extension to download club datset!
# Note: Actual Rarity of each card is now shown.
RARITY_2 = ["Rare"]
NUM_RARITY_2 = [2]  # Total players from i^th Rarity / Color >= NUM_RARITY_2[i]

SQUAD_RATING = 80 # Squad Rating: Min XX

MIN_OVERALL = [83]
NUM_MIN_OVERALL = [1]  # Minimum OVR of XX : Min X

CHEMISTRY = 31  # Squad Total Chemistry Points: Min X
                # If there is no constraint on total chemistry, then set this to 0.

CHEM_PER_PLAYER = 0  # Chemistry Points Per Player: Min X

'''INPUTS'''

formation_dict = {
    "3-4-1-2": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "CAM", "ST", "ST"],
    "3-4-2-1": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "CF", "ST", "CF"],
    "3-1-4-2": ["GK", "CB", "CB", "CB", "LM", "CM", "CDM", "CM", "RM", "ST", "ST"],
    "3-4-3": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "CAM", "ST", "ST"],
    "3-5-2": ["GK", "CB", "CB", "CB", "CDM", "CDM", "LM", "CAM", "RM", "ST", "ST"],
    "3-4-3": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "LW", "ST", "RW"],
    "4-1-2-1-2": ["GK", "LB", "CB", "CB", "RB", "CDM", "LM", "CAM", "RM", "ST", "ST"],
    "4-1-2-1-2[2]": ["GK", "LB", "CB", "CB", "RB", "CDM", "CM", "CAM", "CM", "ST", "ST"],
    "4-1-4-1": ["GK", "LB", "CB", "CB", "RB", "CDM", "LM", "CM", "CM", "RM", "ST"],
    "4-2-1-3": ["GK", "LB", "CB", "CB", "RB", "CDM", "CDM", "CAM", "LW", "ST", "RW"],
    "4-2-3-1": ["GK", "LB", "CB", "CB", "RB", "CDM", "CDM", "CAM", "CAM", "CAM", "ST"],
    "4-2-3-1[2]": ["GK", "LB", "CB", "CB", "RB", "CDM", "CDM", "CAM", "LM", "ST", "RM"],
    "4-2-2-2": ["GK", "LB", "CB", "CB", "RB", "CDM", "CDM", "CAM", "CAM", "ST", "ST"],
    "4-2-4": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "LW", "ST", "ST", "RW"],
    "4-3-1-2": ["GK", "CB", "CB", "LB", "RB", "CM", "CM", "CM", "CAM", "ST", "ST"],
    "4-1-3-2": ["GK", "LB", "CB", "CB", "RB", "CDM", "LM", "CM", "RM", "ST", "ST"],
    "4-3-2-1": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "CF", "ST", "CF"],
    "4-3-3": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "LW", "ST", "RW"],
    "4-3-3[2]": ["GK", "LB", "CB", "CB", "RB", "CM", "CDM", "CM", "LW", "ST", "RW"],
    "4-3-3[3]": ["GK", "LB", "CB", "CB", "RB", "CDM", "CDM", "CM", "LW", "ST", "RW"],
    "4-3-3[4]": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CAM", "LW", "ST", "RW"],
    "4-3-3[5]": ["GK", "LB", "CB", "CB", "RB", "CDM", "CM", "CM", "LW", "CF", "RW"],
    "4-4-1-1": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "LM", "CF", "RM", "ST"],
    "4-4-1-1[2]": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "LM", "CAM", "RM", "ST"],
    "4-4-2": ["GK", "LB", "CB", "CB", "RB", "LM", "CM", "CM", "RM", "ST", "ST"],
    "4-4-2[2]": ["GK", "LB", "CB", "CB", "RB", "LM", "CDM", "CDM", "RM", "ST", "ST"],
    "4-5-1": ["GK", "CB", "CB", "LB", "RB", "CM", "LM", "CAM", "CAM", "RM", "ST"],
    "4-5-1[2]": ["GK", "CB", "CB", "LB", "RB", "CM", "LM", "CM", "CM", "RM", "ST"],
    "5-2-1-2":["GK", "LWB", "CB", "CB", "CB", "RWB", "CM", "CM", "CAM", "ST", "ST"],
    "5-2-2-1": ["GK", "LWB", "CB", "CB", "CB", "RWB", "CM", "CM", "LW", "ST", "RW"],
    "5-3-2": ["GK", "LWB", "CB", "CB", "CB", "RWB", "CM", "CDM", "CM", "ST", "ST"],
    "5-4-1": ["GK", "LWB", "CB", "CB", "CB", "RWB", "CM", "CM", "LM", "RM", "ST"]
    }

status_dict = {
    0: "UNKNOWN: The status of the model is still unknown. A search limit has been reached before any of the statuses below could be determined.",
    1: "MODEL_INVALID: The given CpModelProto didn't pass the validation step.",
    2: "FEASIBLE: A feasible solution has been found. But the search was stopped before we could prove optimality.",
    3: "INFEASIBLE: The problem has been proven infeasible.",
    4: "OPTIMAL: An optimal feasible solution has been found."
}

def calc_squad_rating(rating):
    '''https://www.reddit.com/r/EASportsFC/comments/5osq7k/new_overall_rating_figured_out'''
    rat_sum = sum(rating)
    avg_rat = rat_sum / NUM_PLAYERS
    excess = sum(max(rat - avg_rat, 0) for rat in rating)
    return round(rat_sum + excess) // NUM_PLAYERS

LOG_RUNTIME = True
