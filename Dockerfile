FROM ubuntu:latest

# Create home directory
RUN mkdir /home/MkvScripts

# Copy files
COPY . /home/MkvScripts
WORKDIR /home/MkvScripts

# Update and install dependencies
RUN apt-get update

# Install mkvtoolnix and cron
RUN apt-get install -y mkvtoolnix mediainfo cron

# Setup Volume
VOLUME ["/storage"]

# set entrypoint
CMD ["cron", "-f"]