import optimize
import pandas as pd


if __name__ == "__main__":
    dataset = "intput.xlsx"
    df = pd.read_excel(dataset)
    players = optimize.SBC(df) # IDs of selected players
    df_out = df.iloc[players]
    df_out.to_excel("output.xlsx", index=False)
