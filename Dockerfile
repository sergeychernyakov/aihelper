# Use Ubuntu 20.04 as a parent image
FROM ubuntu:20.04

# Set the working directory in the container to /aihelper
WORKDIR /aihelper

# Install Python and other dependencies
# Set DEBIAN_FRONTEND to noninteractive to disable interactive prompts
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3.9 \
    python3-pip \
    libgl1-mesa-glx \
    libopencv-dev \
    ffmpeg \
    libpq-dev \
    poppler-utils \
    antiword \
    tesseract-ocr \
    tesseract-ocr-eng \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /aihelper
COPY . /aihelper

# Install Python dependencies
# Exclude problematic packages from requirements.txt and install them separately if needed
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN git status

# Remove or comment out the installation of pypdfium2 if it causes issues
RUN pip install --no-deps pypdfium2==4.24.0 && \
    pip install --no-deps textract==1.6.5

# Make port 443 available to the world outside this container
EXPOSE 443

# Run app.py when the container launches
# CMD ["/aihelper/start_bots.sh"]
CMD ["python3", "/aihelper/diet_bot.py"]
# CMD ["python3", "/aihelper/translator_bot.py"]
