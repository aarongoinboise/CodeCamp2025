# Requirements
## 📦 Requirements for Running Jupyter Notebooks and Python Files

To ensure everything works smoothly with both your Jupyter notebooks and supporting `.py` files, make sure the following are installed:

- **Python 3.x**  
  Make sure you’re running Python 3 (currently running Python 3.12.3).  
  🛠️ Check with: `python --version`

- **pip**  
  Python package installer.  
  🛠️ Check with: `pip --version`

- **Jupyter Notebook**  
  Core tool for running `.ipynb` files.  
  🛠️ Install with: `pip install notebook`

- **virtualenv (optional but recommended)**  
  For managing isolated environments.  
  🛠️ Install with: `pip install virtualenv`

- **Recommended for later:**
  - `numpy`
  - `pandas`\
  🛠️ Install with:  
  ```bash
  pip install numpy pandas


## 📁 Directory Structure & Notebook Order

🛑 **Do not move or rename folders/files** — the code depends on the existing relative paths.

### 🏈 Fantasy Football Notebooks (in order):

1. `ff/non_player_data_clean.ipynb`  
   *(Cleans general league data)*

2. `ff/position_clean.ipynb`  
   *(Processes position-specific player data)*

3. `ff/model_select-train-test.ipynb`  
   *(Selects, trains, and evaluates models)*

### 🏀 College Basketball Notebook:

- `cb/cb.ipynb`  
  *(Full data processing and modeling in one notebook using a pre-trained model)*

Please take note of the sources in the notebooks, and respect web-scraping policies of websites. Pretty please.
