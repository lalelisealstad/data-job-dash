# Use the official Python base image
FROM python:3.12.0

WORKDIR /app

COPY . .

# Create a virtual environment and activate it
RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Specify the command to run the app
CMD ["python" , "app.py", "--host=0.0.0.0", "--port=8080"]

EXPOSE 8080