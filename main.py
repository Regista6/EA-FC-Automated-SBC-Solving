import input
import optimize
import pandas as pd

# Preprocess the club dataset obtained from https://github.com/ckalgos/fut-trade-enhancer.
def preprocess_data_1(df: pd.DataFrame):
    df = df.drop(['Price Range', 'Bought For', 'Discard Value', 'Contract Left'], axis = 1)
    df = df.rename(columns={'Player Name': 'Name', 'Nation': 'Country', 'Quality': 'Color', 'FUTBIN Price': 'Cost'})
    df = df[df["IsUntradable"] == True]
    df = df[df["IsLoaned"] == False]
    df = df[df["Cost"] != '--NA--']
    # Note: The filter on rating is especially useful when there is only a single constraint like Squad Rating: Min XX.
    # Otherwise, the search space is too large and this overwhelms the solver (very slow in improving the bound).
    # df = df[(df["Rating"] >= input.SQUAD_RATING - 3) & (df["Rating"] <= input.SQUAD_RATING + 3)]
    df = df.reset_index(drop = True).astype({'Rating': 'int32', 'Cost': 'int32'})
    return df

# Preprocess the club dataset obtained from https://chrome.google.com/webstore/detail/fut-enhancer/boffdonfioidojlcpmfnkngipappmcoh.
# Datset obtained from here has the extra columns [IsDuplicate, IsInActive11].
# So duplicates can be prioritized now if needed.
def preprocess_data_2(df: pd.DataFrame):
    df = df.drop(['Price Limits', 'Last Sale Price', 'Discard Value', 'Contract', 'DefinitionId'], axis = 1)
    df = df.rename(columns={'Nation': 'Country', 'Team' : 'Club', 'Preferred Position': 'Position', 'ExternalPrice': 'Cost'})
    df["Color"] = df["Rating"].apply(lambda x: 'Bronze' if x < 65 else ('Silver' if 65 <= x <= 74 else 'Gold'))
    df.insert(2, 'Color', df.pop('Color'))
    df = df[df["Untradeable"] == True]
    df = df[df["IsInActive11"] != True]
    df = df[df["Loans"] == False]
    df = df[df["Cost"] != '-- NA --']
    df = df[df["Cost"] != '0']
    # Note: The filter on rating is especially useful when there is only a single constraint like Squad Rating: Min XX.
    # Otherwise, the search space is too large and this overwhelms the solver (very slow in improving the bound).
    # df = df[(df["Rating"] >= input.SQUAD_RATING - 3) & (df["Rating"] <= input.SQUAD_RATING + 3)]
    df = df.reset_index(drop = True).astype({'Rating': 'int32', 'Cost': 'int32'})
    return df

if __name__ == "__main__":
    dataset = "Catamarca FC.csv"
    df = pd.read_csv(dataset, index_col = False)
    # df = preprocess_data_1(df)
    df = preprocess_data_2(df)
    # df.to_excel("club_preprocessed.xlsx", index = False)
    final_players = optimize.SBC(df)
    if final_players:
        df_out = df.iloc[final_players]
        print(f"Total Chemistry: {df_out['Chemistry'].sum()}")
        print(f"Total Cost: {df_out['Cost'].sum()}")
        df_out.to_excel("output.xlsx", index = False)
