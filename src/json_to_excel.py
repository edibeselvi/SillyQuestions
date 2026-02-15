import os
import json
import pandas as pd
import glob

def main():
    root_dir = os.path.join(os.getcwd(), "outputs")
    if not os.path.exists(root_dir):
        print(f"Error: Output directory '{root_dir}' not found.")
        return
    records = []

    print(f"Scanning directories in: {root_dir}")

    # Walk through logical directories
    for folder_name in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, folder_name)
        
        # Check if it's a directory
        if not os.path.isdir(folder_path):
            continue

        # Check for json files in the directory matching soru_*.json
        json_files = glob.glob(os.path.join(folder_path, "soru_*.json"))
        
        if not json_files:
            continue

        print(f"Processing model folder: {folder_name}")

        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extract fields
                    # Model name from folder name (as requested)
                    model_name = folder_name
                    
                    # Question ID usually in data['question_id'] or filename
                    q_id = data.get('question_id')
                    
                    # Navigate to result
                    result = data.get('result', {})
                    answer = result.get('answer', '')
                    duration = result.get('duration_seconds', 0)
                    token_usage = result.get('token_usage', {})
                    completion_tokens = token_usage.get('completion_tokens', 0)

                    records.append({
                        'Model': model_name,
                        'Question': q_id,
                        'Answer': answer,
                        'Duration': duration,
                        'Tokens': completion_tokens
                    })

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    if not records:
        print("No records found.")
        return

    # Create Master DataFrame
    df = pd.DataFrame(records)

    # Sort by Question ID just in case
    df.sort_values(by=['Model', 'Question'], inplace=True)

    # Pivot Tables
    # Pivot for Answers
    try:
        df_answers = df.pivot(index='Model', columns='Question', values='Answer')
    except Exception as e:
        print(f"Error creating pivot for Answers: {e}")
        df_answers = pd.DataFrame()

    # Pivot for Duration
    try:
        df_duration = df.pivot(index='Model', columns='Question', values='Duration')
    except Exception as e:
        print(f"Error creating pivot for Duration: {e}")
        df_duration = pd.DataFrame()
        
    # Pivot for Tokens
    try:
        df_tokens = df.pivot(index='Model', columns='Question', values='Tokens')
    except Exception as e:
        print(f"Error creating pivot for Tokens: {e}")
        df_tokens = pd.DataFrame()

    output_file = os.path.join(root_dir, 'model_evaluation_report.xlsx')
    
    print(f"Writing to {output_file}...")
    
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df_answers.to_excel(writer, sheet_name='Answers')
            df_duration.to_excel(writer, sheet_name='Duration')
            df_tokens.to_excel(writer, sheet_name='Completion Tokens')
        print("Success! Excel file created.")
    except Exception as e:
        print(f"Error writing Excel file: {e}")

if __name__ == "__main__":
    main()
