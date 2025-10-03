FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /workspace

# Upgrade pip to the latest version
RUN python -m pip install --upgrade pip

# Install any needed packages specified in requirements.txt
COPY ./requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt

# Copy the app directory to the workspace
COPY ./app /workspace/app

# Run app.py when the container launches
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
