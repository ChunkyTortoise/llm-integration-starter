FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
COPY README.md .
RUN pip install --no-cache-dir -e .
EXPOSE 8501
CMD ["streamlit", "run", "src/llm_starter/demo/app.py", "--server.port=8501", "--server.headless=true"]
