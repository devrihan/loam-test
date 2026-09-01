# LOAM Data Validator

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/devrihan/loam-test.git
   cd loam-test
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Install requirements**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright**
   ```bash
   playwright install
   ```

5. **Add `.env` file**
   Create a `.env` file in the project root:
   ```env
   LOAM_USERNAME=your_username
   LOAM_PASSWORD=your_password
   LOAM_BASE_URL=https://dps.inferentics.com/login
   ```

6. **Add Master Excel**
   Create a `master_data` folder in the project root and place the required Master Excel file inside it. 
   
   *Example:*
   ```text
   master_data/
   └── Class11_UnitTest1_Analysis_202627.xlsx
   ```

7. **Run the validator**
   ```bash
   python main.py --master ".\master_data\Class11_UnitTest1_Analysis_202627.xlsx" --subject "Accountancy" --grade-section "11-C"
   ```
   
   *Example for another class:*
   ```bash
   python main.py --master ".\master_data\Class12_UnitTest1_Analysis_202627.xlsx" --subject "Accountancy" --grade-section "12-C"
   ```

