# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory in the container to /app
WORKDIR /app

# Copy the directory contents into the container at /app
COPY . /app

# Copy the config file into the container
#COPY config.yaml /etc/concertim-openstack-service/config.yaml

# Install any needed packages specified in requirements-userhandler.txt
RUN pip install --no-cache-dir -r user_handler/requirements-userhandler.txt

# Create logging diretory
RUN mkdir -p /var/log/concertim-openstack-service

# Make port 42356 available to the world outside this container
EXPOSE 42356

# Run user_handler when the container launches
CMD ["python", "run_user_handler.py"]
