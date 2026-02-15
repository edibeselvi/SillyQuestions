import pandas as pd
import json
import os

def process_data():
    base_dir = os.getcwd()
    questions_file = os.path.join(base_dir, 'data', 'sorular.txt')
    excel_file = os.path.join(base_dir, 'outputs', 'model_evaluation_report.xlsx')
    output_dir = os.path.join(base_dir, 'outputs', 'web')
    output_file = os.path.join(output_dir, 'data.json')

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 1. Read Questions
    try:
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(questions)} questions.")
    except Exception as e:
        print(f"Error reading questions file: {e}")
        return

    # 2. Read Excel Data
    try:
        # Read Excel, treating 1-10 as headers potentially or mapping them
        df = pd.read_excel(excel_file)
        print(f"Loaded Excel with columns: {df.columns.tolist()}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # 3. Structure Data
    # Expected Excel columns: 'Model', 1, 2, ..., 10
    # Questions list index 0 -> Column 1, Index 1 -> Column 2
    
    results = []
    
    for index, row in df.iterrows():
        model_name = row['Model']
        model_answers = []
        
        # Iterate through question columns (assuming they are named 1 through 10)
        # We need to map the question text to the answer
        
        # Check if columns are integers 1-10 or strings '1'-'10'
        # The inspect output showed: ['Model', 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] (integers)
        
        for i in range(1, 11):
            if i in df.columns:
                answer = row[i]
                # Handle NaN
                if pd.isna(answer):
                    answer = "No answer provided."
                model_answers.append(str(answer))
            else:
                model_answers.append("Column not found")

        results.append({
            "model": model_name,
            "answers": model_answers # simple list corresponding to questions index
        })

    final_data = {
        "questions": questions,
        "results": results
    }

    # 4. Save to JSON
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved data to {output_file}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

if __name__ == "__main__":
    process_data()
