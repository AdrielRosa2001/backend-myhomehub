FROM python:3.12-slim

WORKDIR /app

# Instala dependências do sistema necessárias para compilar pacotes (como o bcrypt)
RUN apt-get update && apt-get install -y gcc libffi-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

EXPOSE 8000

# Rodamos o uvicorn com APENAS 1 worker para economizar RAM
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]