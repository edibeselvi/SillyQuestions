# Model Evaluation Pipeline (Turkish LLM Perspective)

This repository contains tools and data for evaluating Large Language Models (LLMs) with a specific focus on Turkish language capabilities and cultural context. It accompanies the article:
**There Are No Silly Questions: Evaluation of Offline LLM Capabilities from a Turkish Perspective** (located in `docs/`).

## 📂 Project Structure

The repository is organized as follows:

- **`src/`**: Python scripts for the evaluation pipeline.
- **`data/`**: Input data files (questions, model lists, rubrics).
- **`outputs/`**: Generated results, including model-specific JSON logs and the final Excel report.
- **`docs/`**: Documentation and the original article PDF.
- **`images/`**: Supporting images (e.g., configuration screenshots).



## 🌐 Web Interface

In addition to the offline evaluation pipeline, the questions, evaluated models, and their generated answers can be viewed through a dedicated web interface for clearer and more user-friendly visualization.

You can explore the questions and model responses here:

🔗 https://edibeselvi.github.io/sq

This interface allows easier browsing and comparison of model outputs in a structured and readable format.


---

## 💻 System Information 

The experiments in this repository were conducted on the following machine:

| Property | Details |
|----------|---------|
| **OS Name** | Microsoft Windows 11 Home |
| **Version** | 10.0.26200 Build 26200 |
| **System Manufacturer** | LENOVO |
| **System Model** | 82RB |
| **System Type** | x64-based PC |
| **Processor** | 12th Gen Intel(R) Core(TM) i7-12700H, 2.3 GHz, 14 Core(s), 20 Logical Processor(s) |
| **Installed RAM** | 40.0 GB (39.7 GB usable) |



---









## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Required libraries: `pandas`, `requests`, `openpyxl`

```bash
pip install pandas requests openpyxl
```

- **LM Studio** (for running evaluations): Ensure LM Studio is installed and the local server is running (usually at `http://127.0.0.1:1234`).

### Usage

**Note:** Always run scripts from the **root directory** of the repository.

#### 1. Evaluate Models
To run the evaluation pipeline using the models listed in `data/llms.txt` and questions in `data/sorular.txt`:

```bash
python src/model_evaluator.py
```
*This will create subdirectories in `outputs/` for each model, containing JSON files for every question-answer pair.*

#### 2. Generate Excel Report
To consolidate all JSON logs into a single Excel file (`outputs/model_evaluation_report.xlsx`):

```bash
python src/json_to_excel.py
```

#### 3. Process Data for Web/Analysis
To process the Excel report and questions into a JSON format suitable for web visualization (`outputs/web/data.json`):

```bash
python src/process_data.py
```

## 📊 Data & Configuration

- **Models**: Edit `data/llms.txt` to add or remove model identifiers (must match LM Studio model IDs).
- **Questions**: Edit `data/sorular.txt` to modify the evaluation dataset.
- **Rubrics**: See `data/rubrik.xlsx` for evaluation criteria.

## 📝 License
This project is for research and educational purposes.
