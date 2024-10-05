FROM python:3.9-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory
WORKDIR /app

# Copy the requirements file first (this allows Docker to cache the installed packages if requirements don't change)
COPY requirements.txt .

# Install the required Python packages
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure setup.sh is executable
RUN chmod +x setup.sh

# Run the setup script (if necessary)
RUN ./setup.sh

# Run the bot
CMD ["python", "bot.py"]
