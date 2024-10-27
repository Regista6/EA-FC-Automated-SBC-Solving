## EA FC Automated [SBC](https://fifauteam.com/sbc-football-club-24/) Solving ⚽ [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1KoP-8zvbeh_0IjOIlrTG-u1j_QPP5DNo?usp=sharing)

### How does this work? 🚂

This project utilizes [integer programming](https://en.wikipedia.org/wiki/Integer_programming) to solve squad building challenges (SBCs). The optimization problem is solved using [Google CP-SAT solver](https://developers.google.com/optimization/cp/cp_solver).
This approach offers extensive customization capabilities, alongside the ability to determine solution optimality.

`The goal is to obtain the squad with the minimum total cost.`

### How to use it? 🔧

- To download the club dataset, use the [extension](https://chrome.google.com/webstore/detail/fut-enhancer/boffdonfioidojlcpmfnkngipappmcoh) (version >= 1.1.0.3).

- The inputs to the different constraints can be found in the `input.py`. Configure the appropriate inputs for each SBC constraint in `input.py` (`L43-77` and `L28-30`) and then navigate to `optimize.py (L581-615)` and uncomment the relevant line based on the SBC requirements. Also don't forget to set the `formation` in `input.py`!

- For example, if the requirement is `Same League Count: Max 5` or `Max 5 Players from the Same League` then set `MAX_NUM_LEAGUE = 5` (`L53` in `input.py`) and then uncomment `model = create_max_league_constraint(df, model, player, map_idx, players_grouped, num_cnts)` (`L589` in `optimize.py`).

- If the requirement is `Nations: Max 2` then set `NUM_UNIQUE_COUNTRY = [2, "Max"]` (`L62` in `input.py`) and then uncomment `model = create_unique_country_constraint(df, model, player, map_idx, players_grouped, num_cnts)` (`L598` in `optimize.py`).

- If you are prioritizing duplicates by setting (`L28-L30`) in `input.py` then `model = prioritize_duplicates(df, model, player)` in `optimize.py` (`L615`) should be uncommented.

- If for instance, the SBC wants `at least 3 players from Real Madrid and Arsenal combined` and `at least 2 players from Bayern Munich`, then set
`CLUB = [["Real Madrid", "Arsenal"], ["FC Bayern"]]` and `NUM_CLUB = [3, 2]` (`L43-44` in `input.py`) and then uncomment `model = create_club_constraint(df, model, player, map_idx, players_grouped, num_cnts)` (`L581` in `optimize.py`).

- If the SBC requires at least `6 Rare` and `8 Gold` then set `RARITY_2 = ["Rare", "Gold"]`and `NUM_RARITY_2 = [6, 8]` in `input.py (L71-72)` and then uncomment `model = create_rarity_2_constraint(df, model, player, map_idx, players_grouped, num_cnts)` (`L603` in `optimize.py`).

- Constraints such as `Chemistry` (`optimize.py`, `L620`) or `FIX_PLAYERS` (`optimize.py`, `L623`) do not require explicit activation. If there is no need for `Chemistry`, set it to `0` in `input.py (L79)`. Similarly, if no players need fixing, leave `FIX_PLAYERS` empty in `input.py (L12)`.

- The `objective` is set in `optimize.py` (`L626`). The nature of the `objective` can be changed in `input.py` (`L20-21`). Currently the objective is to `minimize` the `total cost`.

- Additional parameters in `input.py` should be reviewed for more information.

- In `main.py`, specify the name of the `club dataset` in `L57`. The dataset is preprocessed in `preprocess_data_2` within `main.py`. Additional filters can be added in a manner similar to the existing ones.

- Currently the inputs are set to solve [this](https://www.futbin.com/25/squad-building-challenge/ea/220/Total%20Rush%20Challenge%206) SBC challenge. The final list of players is written into the file `output.xlsx`. To execute the program, simply run `py main.py` after installing the required dependencies. Note: This seems to be a very hard SBC and so had to enable the filter on rating in `main.py (L41)`.

### Dependencies 🖥️

Run `pip3 install -r requirements.txt` to install the required dependencies.

- [Google OR-Tools v9.8](https://github.com/google/or-tools)

- Python 3.9

- pandas and openpyxl

### Other Interesting Open-Source SBC Solvers ⚙️

- https://github.com/ThomasSteere/Auto-SBC

- https://github.com/bartlomiej-niemiec/eafc-sbc-solver

- https://github.com/kosciukiewicz/sbc-solver

### Acknowledgement 🙏

Thank you `GregoryWullimann` for making the model creation process [insanely faster](https://github.com/Regista6/EA-FC-24-Automated-SBC-Solving/pull/3).

Thank you `Jacobi from EasySBC` for helping with the `squad_rating_constraint`.

Thank you `GeekFiro` for testing the solver and providing valuable feedback and discussions.

Thank you `fifagamer#1515` and `Frederik` for providing your club datasets (`Real_Madrid_FC_24.csv` and `Frederik FC_24.csv`) and your feedback.

Thank you `ckalgos` for creating the extension to download club dataset.

Thank you `drRobertDev` for providing the dataset `Fc25Players.csv`.

Thank you to everyone who have opened issues on the repo and provided their feedback.

Thank you to all the folks who commented on the [reddit post](https://www.reddit.com/r/fut/comments/15hxy2p/open_source_sbc_solver/).

Thank you FutDB for providing the API which allowed me to test the solver originally on 10k players (`input.csv`)