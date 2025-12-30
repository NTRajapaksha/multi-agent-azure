# 1. Base Image: Use a lightweight Python version
FROM python:3.10-slim

# 2. Set the Working Directory inside the container
WORKDIR /app

# 3. Environment Variables (Keeps Python from buffering stdout)
ENV PYTHONUNBUFFERED=1

# 4. Copy Dependencies first (Leverages Docker Layer Caching)
COPY requirements.txt .

# 5. Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code
COPY . .

# 7. Expose the port the app runs on
EXPOSE 8000

# 8. Command to run the application
# We use the python command because your main.py has the uvicorn.run block
CMD ["python", "main.py"]