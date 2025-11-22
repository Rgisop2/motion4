FROM python:3.10-slim

# Optional: update and install git only if needed
# If your requirements.txt has NO "git+" lines, remove this part.
RUN apt-get update && apt-get install -y git && apt-get clean

WORKDIR /app

# Copy dependencies file
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Start the bot
CMD ["python3", "bot.py"]
