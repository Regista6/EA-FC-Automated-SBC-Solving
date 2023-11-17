## EA FC 24 Automated [SBC](https://fifauteam.com/fifa-23-sbc/) Solving ⚽ [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1KoP-8zvbeh_0IjOIlrTG-u1j_QPP5DNo?usp=sharing)

### Notes

The project utilizes a dataset of 10,000 players (`input.csv`) obtained from [FutDB](https://futdb.app)
along with their respective prices, as the input source. The data has been also manually tinkered with to fill in some of the gaps.

`The goal is to obtain the squad with the minimum cost.`

The dataset serves as a `proof-of-concept demonstration` of the system's functionality, however, it is ideal to have a real-time dataset that includes the entire club of the user along with the player prices. In other words, the program is only as good as the data.

Update: I was able to import my club's dataset (`Catamarca FC_24.csv`) from [here](https://chrome.google.com/webstore/detail/fut-enhancer/boffdonfioidojlcpmfnkngipappmcoh).

Update 1: Thanks `fifagamer#1515` for your club dataset `Real_Madrid_FC_24.csv`.

The inputs to the different constraints can be found in the `input.py` file.

The constraints used in the program are created in the `optimize.py` file and the optimization problem is solved using [Google CP-SAT solver](https://developers.google.com/optimization/cp/cp_solver).

The program implements most of the common constraints (`L539-575` in `optimize.py`). Feel free to comment out the constraints that are not required.

Currently the inputs are set to solve [this](https://www.futbin.com/squad-building-challenges/ALL/38/fiendish) SBC challenge. The final list of players is written into the file `output.xlsx`.

To execute the program, simply run `py main.py` after installing the required dependencies.

### Dependencies

Run `pip3 install -r requirements.txt` to install the required dependencies.

- [Google OR-Tools v9.8](https://github.com/google/or-tools)

- Python 3.9

- pandas and openpyxl
