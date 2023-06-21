# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory in the container to /app
WORKDIR /app

# Add the parent directory contents into the container at /app
ADD .. /app

# Install any needed packages specified in requirements-userhandler.txt
RUN pip install --no-cache-dir -r requirements-userhandler.txt

# Make port 42356 available to the world outside this container
EXPOSE 42356

# Run user_handler when the container launches
CMD ["python", "run_user_handler.py"]