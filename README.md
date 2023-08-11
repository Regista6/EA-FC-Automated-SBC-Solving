## FIFA 23 Automated [SBC](https://fifauteam.com/fifa-23-sbc/) Solving ⚽

### Notes

The project utilizes a dataset of 10,000 players (`input.csv`) obtained from [FutDB](https://futdb.app)
along with their respective prices, as the input source. The data has been also manually tinkered with to fill in some of the gaps.

`The goal is to obtain the squad with the minimum cost.`

The dataset serves as a `proof-of-concept demonstration` of the system's functionality, however, it is ideal to have a real-time dataset that includes the entire club of the user along with the player prices. In other words, the program is only as good as the data.

Update: I was able to import my club's dataset (`Catamarca FC.csv`) from [here](https://github.com/ckalgos/fut-trade-enhancer).

The inputs to the different constraints can be found in the `input.py` file. Currently, the program works for 11 players only.

Please note that it will require some amount of manual post-processing if there are constraints involving cards that are not there in the dataset or if some constraints haven't been implemented.

The constraints used in the program are created in the `optimize.py` file and the optimization problem is solved using [Google CP-SAT solver](https://developers.google.com/optimization/cp/cp_solver).

The program implements most of the common constraints (`L487-519` in `optimize.py`). Feel free to comment out the constraints that are not required.

Also please note the type of constraint sign used (i.e., >=, <=, ==) for each constraint in the `optimize.py` file during input.

Currently the inputs are set to solve [this](https://www.futbin.com/squad-building-challenges/EXPIRED/1576/outstanding) SBC challenge. The final list of players is written into the file `output.xlsx`.

To execute the program, simply run `py main.py` after installing the required dependencies.

### Dependencies

Run `pip3 install -r requirements.txt` to install the required dependencies.

- [Google OR-Tools v9.6](https://github.com/google/or-tools)

- Python 3.9

- pandas and openpyxl
