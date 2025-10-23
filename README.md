### Comandos para executar o projeto
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app src/main.py db upgrade
flask --app src/main.py run --debug
```