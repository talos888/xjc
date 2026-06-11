# Runner Environment

The runner environment is separate from paper-reading or image-reading skills.

Runner dependencies:

- `mph`
- `JPype1`
- `numpy`
- `PyYAML` only when optional YAML manifests are used

Do not add PDF/OCR/Zotero dependencies such as `pypdf` to this runner unless the
runner itself starts reading documents. Paper parsing belongs to upstream
problem-spec or model-planner skills.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy templates\runner_config.example.json runner_config.json
```

Edit `runner_config.json`, then run:

```powershell
.\.venv\Scripts\python.exe scripts\check_environment.py
```

To also start COMSOL and consume a license:

```powershell
.\.venv\Scripts\python.exe scripts\check_environment.py --start-comsol
```
