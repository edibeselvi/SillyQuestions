import requests
import json
import os
import time
from pathlib import Path

class ModelEvaluator:
    def __init__(self, api_base_url="http://127.0.0.1:1234", llms_file="llms.txt", questions_file="sorular.txt"):
        self.api_base_url = api_base_url.rstrip('/')
        self.chat_url = f"{self.api_base_url}/v1/chat/completions"
        self.models_url = f"{self.api_base_url}/v1/models"
        self.llms_file = llms_file
        self.questions_file = questions_file
        self.timeout = 300 # 5 minutes timeout for model loading/generation

    def load_file_lines(self, filepath):
        """Reads non-empty lines from a file."""
        if not os.path.exists(filepath):
            print(f"HATA: '{filepath}' dosyası bulunamadı.")
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        return lines

    def check_api_connection(self):
        """Checks if LM Studio API is accessible."""
        try:
            requests.get(self.models_url, timeout=5)
            return True
        except requests.RequestException:
            print(f"HATA: LM Studio API'ye ({self.api_base_url}) bağlanılamadı. Server açık mı?")
            return False

    def query_model(self, model_name, question):
        """Sends a query to the model and returns result + stats."""
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "Sen yardımcı bir asistansın."},
                {"role": "user", "content": question}
            ],
            "temperature": 0.7,
            "stream": False
        }

        start_time = time.time()
        try:
            print(f"  - İstek gönderiliyor: '{model_name}' modeline...")
            response = requests.post(self.chat_url, json=payload, headers={"Content-Type": "application/json"}, timeout=self.timeout)
            end_time = time.time()
            
            duration = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                usage = result.get('usage', {})
                
                return {
                    "success": True,
                    "answer": content,
                    "duration_seconds": round(duration, 4),
                    "token_usage": {
                        "prompt_tokens": usage.get('prompt_tokens', 0),
                        "completion_tokens": usage.get('completion_tokens', 0),
                        "total_tokens": usage.get('total_tokens', 0)
                    },
                    "model_response_id": result.get('id', '')
                }
            else:
                return {
                    "success": False,
                    "error": f"API Hatası: {response.status_code} - {response.text}",
                    "duration_seconds": round(duration, 4)
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Zaman aşımı (Timeout)",
                "duration_seconds": round(time.time() - start_time, 4)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": round(time.time() - start_time, 4)
            }

    def run(self):
        """Main execution loop."""
        print("LM Studio Model Evaluator Başlatılıyor...")
        
        if not self.check_api_connection():
            return

        models = self.load_file_lines(self.llms_file)
        questions = self.load_file_lines(self.questions_file)

        if not models:
            print("HATA: Hiç model bulunamadı (llms.txt boş mu?).")
            return
        if not questions:
            print("HATA: Hiç soru bulunamadı (sorular.txt boş mu?).")
            return

        print(f"BİLGİ: {len(models)} model ve {len(questions)} soru yüklendi.")

        for model_name in models:
            print(f"\n{'='*60}")
            print(f"MODEL DEVRİYE ALINIYOR: {model_name}")
            print(f"{'='*60}")
            
            # Create/Ensure directory exists for the model
            # Sanitize model name for folder path (replace invalid chars)
            safe_model_name = "".join(x for x in model_name if x.isalnum() or x in "-_.")
            model_folder = os.path.join(os.getcwd(), safe_model_name)
            os.makedirs(model_folder, exist_ok=True)
            print(f"KLASÖR OLUŞTURULDU: {model_folder}")

            # Note: In LM Studio, making a request with "model": "id" usually attempts to load it 
            # if it's not loaded, BUT it might require the user to have downloaded it first.
            # We trigger the first 'dummy' call or just proceed to questions.
            # We will proceed directly to questions, the first one might take longer due to loading.

            for i, question in enumerate(questions, 1):
                print(f"\nSORU {i}/{len(questions)}: {question[:50]}...")
                
                result = self.query_model(model_name, question)
                
                # Prepare JSON content
                output_data = {
                    "question_id": i,
                    "model": model_name,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "question": question,
                    "result": result
                }
                
                # Save to file
                output_filename = f"soru_{i}.json"
                output_path = os.path.join(model_folder, output_filename)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=4, ensure_ascii=False)
                
                if result['success']:
                    print(f"  ✓ TAMAMLANDI ({result['duration_seconds']}s, {result['token_usage']['total_tokens']} tokens)")
                else:
                    print(f"  ❌ HATA: {result.get('error')}")

        print("\n" + "="*60)
        print("TÜM İŞLEMLER TAMAMLANDI")
        print("="*60)

if __name__ == "__main__":
    evaluator = ModelEvaluator()
    evaluator.run()
