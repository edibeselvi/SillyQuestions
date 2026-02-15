import sys
import io

# Force UTF-8 output for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import os
import time
import re
from pathlib import Path

class ResponseEvaluator:
    def __init__(self, api_base_url="http://127.0.0.1:1234", llms_file="llms.txt", rubric_file="rupric.json", prompt_file="prompt.json"):
        self.api_base_url = api_base_url.rstrip('/')
        self.chat_url = f"{self.api_base_url}/v1/chat/completions"
        self.llms_file = llms_file
        self.rubric_file = rubric_file
        self.prompt_file = prompt_file
        self.output_dir = "evaluations"
        self.timeout = 300  # 5 minutes timeout

    def check_api_connection(self):
        """Checks if the Judge model API is accessible and gets the loaded model ID."""
        try:
            response = requests.get(f"{self.api_base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and 'data' in data and len(data['data']) > 0:
                    self.judge_model_id = data['data'][0]['id']
                    print(f"✓ LM Studio API bağlantısı başarılı. Kullanılan Model: {self.judge_model_id}")
                    return True
                else:
                    print("HATA: LM Studio'da yüklü model bulunamadı. Lütfen 'Developer' sekmesinden veya 'lms load' ile bir model yükleyin.")
                    return False
            else:
                print(f"HATA: API erişilebilir ancak model listesi alınamadı (Kod: {response.status_code}).")
                return False
        except requests.RequestException:
            print(f"HATA: LM Studio API'ye ({self.api_base_url}) bağlanılamadı. Judge modelin yüklü ve sunucunun açık olduğundan emin olun.")
            return False

    def load_file_lines(self, filepath):
        if not os.path.exists(filepath):
            print(f"UYARI: '{filepath}' dosyası bulunamadı.")
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    def load_json(self, filepath):
        if not os.path.exists(filepath):
            print(f"HATA: '{filepath}' dosyası bulunamadı.")
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_text(self, filepath):
        if not os.path.exists(filepath):
            print(f"HATA: '{filepath}' dosyası bulunamadı.")
            return ""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def format_rubric(self, rubric_data):
        """Converts the JSON rubric into a readable text format for the prompt."""
        if not rubric_data or "dimensions" not in rubric_data:
            return ""
        
        text = "DETAILED RUBRIC EVALUATION CRITERIA:\n"
        for dim in rubric_data["dimensions"]:
            text += f"\n- **{dim['id']}** ({dim['label']}):\n"
            text += f"  Description: {dim['description']}\n"
            text += "  Scoring:\n"
            for score, desc in dim['score_scale'].items():
                text += f"    {score}: {desc}\n"
        return text

    def get_model_folders(self, model_names):
        """Finds valid folders corresponding to the models."""
        valid_folders = []
        base_dir = os.getcwd()
        
        for name in model_names:
            # Reconstruct the folder name logic from the previous script
            # Logic was: "".join(x for x in model_name if x.isalnum() or x in "-_.")
            safe_name = "".join(x for x in name if x.isalnum() or x in "-_.")
            folder_path = os.path.join(base_dir, safe_name)
            
            if os.path.isdir(folder_path):
                valid_folders.append((name, folder_path))
            else:
                print(f"UYARI: '{name}' için klasör bulunamadı: {safe_name}")
        
        return valid_folders

    def evaluate_single_response(self, judge_prompt):
        """Sends the evaluation prompt to the Judge model."""
        payload = {
            "model": getattr(self, 'judge_model_id', 'local-model'),
            "messages": [
                {"role": "system", "content": "You are a fair and strict AI judge."},
                {"role": "user", "content": judge_prompt}
            ],
            "temperature": 0.0, # Deterministic for evaluation
            "stream": False
        }

        try:
            response = requests.post(self.chat_url, json=payload, headers={"Content-Type": "application/json"}, timeout=self.timeout)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Try to extract JSON from the content if it's wrapped in markdown or extra text
                # Find the first '{' and last '}'
                try:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start != -1 and end != -1:
                        json_str = content[start:end]
                        return json.loads(json_str), content
                    else:
                        return None, content
                except json.JSONDecodeError:
                    return None, content
            else:
                print(f"API Hatası: {response.status_code} - {response.text}")
                return None, f"Error: {response.status_code}"
        except Exception as e:
            print(f"İstek Hatası: {str(e)}")
            return None, str(e)

    def run(self):
        print("Model Response Evaluator Başlatılıyor...")
        
        if not self.check_api_connection():
            return

        # Load resources
        model_names = self.load_file_lines(self.llms_file)
        rubric_json = self.load_json(self.rubric_file)
        prompt_template = self.load_text(self.prompt_file)

        if not model_names or not rubric_json or not prompt_template:
            print("Gerekli dosyalar eksik. İşlem iptal edildi.")
            return

        # Prepare formatting
        rubric_text = self.format_rubric(rubric_json)
        
        # Inject rubric into template
        # Replaces the brief "RUBRIC:\n- ..." list with the detailed one if found, 
        # otherwise just appends/inserts it.
        # Looking at the file content, it has "RUBRIC:" followed by a list.
        # We will split on "RUBRIC:" and replace everything after it until "---" or "OUTPUT FORMAT".
        
        if "RUBRIC:" in prompt_template:
             # Basic replacement: Find the section
            parts = prompt_template.split("RUBRIC:")
            pre_rubric = parts[0]
            # Find where the rubric section ends (next header is 'INPUT' or 'OUTPUT' or '---')
            # In the file viewed: "---" is after the rubric list.
            rest = parts[1]
            if "---" in rest:
                _, post_rubric = rest.split("---", 1)
                final_template = f"{pre_rubric}RUBRIC:\n{rubric_text}\n\n---{post_rubric}"
            else:
                # Fallback
                final_template = f"{pre_rubric}RUBRIC:\n{rubric_text}\n\n{rest}"
        else:
            final_template = prompt_template + "\n\n" + rubric_text

        model_folders = self.get_model_folders(model_names)
        print(f"BİLGİ: {len(model_folders)} model klasörü bulundu.")
        
        # Create output directory
        full_output_dir = os.path.join(os.getcwd(), self.output_dir)
        os.makedirs(full_output_dir, exist_ok=True)

        total_evaluations = 0
        
        for model_name, folder_path in model_folders:
            print(f"\nDEĞERLENDİRİLİYOR: {model_name}")
            
            # Create model specific output folder
            # Keep original structure: maybe separate folder or just in 'evaluations'
            # User output format: "elde ettigi tum skorlari ayri bir klasor icerinde kaydetsin"
            # I will make a subfolder in evaluations/safe_model_name
            safe_model_name = os.path.basename(folder_path)
            model_eval_dir = os.path.join(full_output_dir, safe_model_name)
            os.makedirs(model_eval_dir, exist_ok=True)
            
            # Find all json files in the folder (soru_*.json)
            json_files = [f for f in os.listdir(folder_path) if f.startswith('soru_') and f.endswith('.json')]
            # Sort valid ones by number
            def extract_number(f):
                m = re.search(r'soru_(\d+)', f)
                return int(m.group(1)) if m else 999
            
            json_files.sort(key=extract_number)

            for json_file in json_files:
                file_path = os.path.join(folder_path, json_file)
                
                # Check if already evaluated? existing feature maybe? 
                # For now, overwrite or skip. Let's overwrite.
                
                data = self.load_json(file_path)
                if not data or "result" not in data or not data["result"].get("success"):
                    print(f"  - ATLANDI: {json_file} (Başarısız sonuç veya geçersiz veri)")
                    continue
                
                question_text = data.get("question", "")
                model_answer = data["result"].get("answer", "")
                question_id = data.get("question_id", "unknown")
                
                print(f"  - Soru {question_id} değerlendiriliyor...")
                
                # Construct query
                current_prompt = final_template.replace("{{question}}", question_text)
                current_prompt = current_prompt.replace("{{model_answer}}", model_answer)
                current_prompt = current_prompt.replace("{{question_id}}", str(question_id))
                
                # Evaluate
                eval_json, raw_response = self.evaluate_single_response(current_prompt)
                
                if eval_json:
                    # Save result
                    output_data = {
                        "evaluator_model": "Judge (Local)",
                        "evaluated_model": model_name,
                        "question_id": question_id,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "rubric_scores": eval_json,
                        "original_question": question_text,
                        "original_answer_snippet": model_answer[:200] + "..." if len(model_answer) > 200 else model_answer
                    }
                    
                    save_path = os.path.join(model_eval_dir, f"eval_soru_{question_id}.json")
                    with open(save_path, 'w', encoding='utf-8') as out_f:
                        json.dump(output_data, out_f, indent=4, ensure_ascii=False)
                    print(f"    ✓ Puan: {eval_json.get('total_score', 'N/A')}")
                    total_evaluations += 1
                else:
                    print(f"    ❌ JSON Parse Hatası veya API Hatası.")
                    # Save raw failure for debugging
                    fail_path = os.path.join(model_eval_dir, f"fail_soru_{question_id}.txt")
                    with open(fail_path, 'w', encoding='utf-8') as fail_f:
                        fail_f.write(raw_response)
        
        print("\n" + "="*60)
        print(f"DEĞERLENDİRME TAMAMLANDI. Toplam {total_evaluations} yanıt puanlandı.")
        print(f"Sonuçlar '{self.output_dir}' klasörüne kaydedildi.")

if __name__ == "__main__":
    evaluator = ResponseEvaluator()
    evaluator.run()
