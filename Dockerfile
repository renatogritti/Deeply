FROM python:3.11-slim

WORKDIR /app

# Instalar dependências para psycopg2 e outras bibliotecas
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    default-libmysqlclient-dev \
    pkg-config \
    build-essential \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instalar Gunicorn explicitamente e depois as outras dependências
RUN pip install --no-cache-dir gunicorn==21.2.0 && \
    pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Criar diretório de uploads
RUN mkdir -p uploads && chmod 777 uploads

# Expor a porta onde o Flask irá rodar
EXPOSE 5000

# Variáveis de ambiente padrão
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Verifique se o gunicorn está instalado e seu caminho
RUN which gunicorn || echo "Gunicorn não encontrado!"

# Comando para iniciar a aplicação
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]