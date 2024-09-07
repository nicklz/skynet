# Use the ultrafunk/undetected-chromedriver image as the base
FROM ultrafunk/undetected-chromedriver:latest

# Set the working directory inside the container
WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    fonts-liberation \
    libasound2 \
    libnss3 \
    libx11-6 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libappindicator1 \
    libdbusmenu-glib4 \
    libdbusmenu-gtk3-4 \
    libxrandr2 \
    libgtk-3-0 \
    xdg-utils \
    libu2f-udev \
    ca-certificates \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the Python script and necessary files into the container
COPY app.py .
COPY requirements.txt .
COPY people_batch.json .
COPY header.json .

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Use ENTRYPOINT so arguments can be passed dynamically
ENTRYPOINT ["python3", "app.py"]
