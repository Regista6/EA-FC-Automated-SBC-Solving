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
# Note: Please use >= v1.1.0.3 of the extension.
def preprocess_data_2(df: pd.DataFrame):
    cols_to_drop = ['Id', 'Groups', 'RarityId', 'Price Limits', 'Last Sale Price', 'Discard Value', 'Contract', 'DefinitionId']
    df = df.drop(columns=[col for col in cols_to_drop if col in df.columns])
    df = df.rename(columns={'Nation': 'Country', 'Team' : 'Club', 'ExternalPrice': 'Cost'})
    df["Color"] = df["Rating"].apply(lambda x: 'Bronze' if x < 65 else ('Silver' if 65 <= x <= 74 else 'Gold'))
    df.insert(2, 'Color', df.pop('Color'))
    # df = df[df["Color"] == "Gold"] # Can be used for constraints like Player Quality: Only Gold.
    # df = df[df["Color"] != "Gold"] # Can be used for constraints like Player Quality: Max Silver.
    # df = df[df["Color"] != "Bronze"] # Can be used for constraints like Player Quality: Min Silver.
    df = df[df["Untradeable"] == True]
    df = df[df["IsInActive11"] != True]
    df = df[df["Loans"] == False]
    df = df[df["Cost"] != '-- NA --']
    df = df[df["Cost"] != '0']
    df = df[df["Cost"] != 0]
    df = df[df['Rarity'].isin(['Rare', 'Common'])]
    df['Rarity'] = df['Rarity'].replace('Team of the Week', 'TOTW')
    # Note: The filter on rating is especially useful when there is only a single constraint like Squad Rating: Min XX.
    # Otherwise, the search space is too large and this overwhelms the solver (very slow in improving the bound).
    # df = df[(df["Rating"] >= input.SQUAD_RATING - 1) & (df["Rating"] <= input.SQUAD_RATING + 1)]
    if input.REMOVE_PLAYERS:
        input.REMOVE_PLAYERS = [(idx - 2) for idx in input.REMOVE_PLAYERS if (idx - 2) in df.index]
        df.drop(input.REMOVE_PLAYERS, inplace=True)
    if input.USE_PREFERRED_POSITION:
        df = df.rename(columns={'Preferred Position': 'Position'})
        df.insert(4, 'Position', df.pop('Position'))
    elif input.USE_ALTERNATE_POSITIONS:
        df = df.drop(['Preferred Position'], axis = 1)
        df = df.rename(columns={'Alternate Positions': 'Position'})
        df.insert(4, 'Position', df.pop('Position'))
        df['Position'] = df['Position'].str.split(',')
        df = df.explode('Position') # Creating separate entries of a particular player for each alternate position.
    df['Original_Idx'] = df.index
    df = df.reset_index(drop = True).astype({'Rating': 'int32', 'Cost': 'int32'})
    return df

if __name__ == "__main__":
    dataset = "Frederik FC_24.csv"
    df = pd.read_csv(dataset, index_col = False)
    # df = preprocess_data_1(df)
    df = preprocess_data_2(df)
    # df.to_excel("Club_Pre_Processed.xlsx", index = False)
    final_players = optimize.SBC(df)
    if final_players:
        df_out = df.iloc[final_players].copy()
        df_out.insert(5, 'Is_Pos', df_out.pop('Is_Pos'))
        print(f"Total Chemistry: {df_out['Chemistry'].sum()}")
        squad_rating = input.calc_squad_rating(df_out["Rating"].tolist())
        print(f"Squad Rating: {squad_rating}")
        print(f"Total Cost: {df_out['Cost'].sum()}")
        df_out['Org_Row_ID'] = df_out['Original_Idx'] + 2
        df_out.pop('Original_Idx')
        df_out.to_excel("output.xlsx", index = False)
