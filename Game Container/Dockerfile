# Use the official Python image from the Docker Hub
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Install dependencies for Pygame and other libraries
RUN apt-get update && apt-get install -y \
    python3-dev \
    libsdl1.2-dev \
    libsdl-image1.2-dev \
    libsdl-mixer1.2-dev \
    libsdl-ttf2.0-dev \
    libsmpeg-dev \
    libportmidi-dev \
    libavformat-dev \
    libswscale-dev \
    x11-xserver-utils \
    x11-apps \
    xinit \
    alsa-utils \
    pulseaudio

# Copy the current directory contents into the container at /app
COPY . /app

# Update pip
RUN pip install --upgrade pip

# Install Git
RUN apt-get update && apt-get install -y git

# Clone the neat-python repository from GitHub
RUN git clone https://github.com/CodeReclaimers/neat-python.git /tmp/neat-python

# Install the package from source
RUN pip install /tmp/neat-python

# Install Pygame
RUN pip install --no-cache-dir pygame

# Set display environment variables
ENV DISPLAY=:0
ENV XDG_RUNTIME_DIR=/tmp/runtime-root

# Run a dummy X server to provide display
CMD Xvfb :0 -screen 0 1024x768x24 & \
    xinit /usr/bin/xterm -- :0 -nolisten tcp & \
    python flappy.py
