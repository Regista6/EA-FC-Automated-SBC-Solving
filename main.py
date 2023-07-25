import input
import optimize
import pandas as pd

# Preprocess the club dataset obtained from https://github.com/ckalgos/fut-trade-enhancer.
def preprocess_data(df: pd.DataFrame):
    df = df.drop(['Price Range', 'Bought For', 'Discard Value', 'Contract Left'], axis = 1)
    df = df.rename(columns={'Player Name': 'Name', 'Nation': 'Country', 'Quality': 'Color', 'FUTBIN Price': 'Cost'})
    df = df[df["IsUntradable"] == True]
    df = df[df["IsLoaned"] == False]
    df = df[df["Cost"] != '--NA--']
    # Note: The filter on rating is especially useful when there is only a single constraint like Squad Rating: Min XX.
    # Otherwise, the search space is too large and this overwhelms the solver (very slow in improving the bound).
    # df = df[(df["Rating"] >= input.SQUAD_RATING - 1) & (df["Rating"] <= input.SQUAD_RATING + 1)]
    df = df.reset_index(drop = True).astype({'Rating': 'int32', 'Cost': 'int32'})
    return df

if __name__ == "__main__":
    dataset = "Catamarca FC.csv"
    df = pd.read_csv(dataset, index_col = False)
    df = preprocess_data(df)
    final_players = optimize.SBC(df)
    if len(final_players) > 0:
        df_out = df.iloc[final_players]
        print(f"Total Chemistry: {df_out['Chemistry'].sum()}")
        print(f"Total Cost: {df_out['Cost'].sum()}")
        df_out.to_excel("output.xlsx", index = False)
