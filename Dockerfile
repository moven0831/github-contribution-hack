# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
# Files listed in .dockerignore will be excluded
COPY . .

# Expose port 5000 if the web interface is used
EXPOSE 5000

# Define environment variable for configuration file path (optional, defaults to config.yml)
# ENV CONFIG_PATH=/app/config.yml

# Define environment variable for GitHub Token (MUST be provided at runtime)
# ENV GITHUB_TOKEN=your_github_token_here 

# Run main.py when the container launches
# By default, this runs the contribution logic (hack.make_contributions())
# To run the web interface, override the command when running the container:
# docker run -e GITHUB_TOKEN=<your_token> -p 5000:5000 <image_name> python main.py --web --host 0.0.0.0
CMD ["python", "main.py"] 