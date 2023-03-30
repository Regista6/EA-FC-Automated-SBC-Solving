import optimize
import pandas as pd

if __name__ == "__main__":
    dataset = "input.csv"
    df = pd.read_csv(dataset)
    final_players = optimize.SBC(df)
    if len(final_players) > 0:
        df_out = df.iloc[final_players]
        print(f"Total Chemistry: {df_out['Chemistry'].sum()}")
        print(f"Total Cost: {df_out['Cost'].sum()}")
        df_out.to_excel("output.xlsx", index=False)
