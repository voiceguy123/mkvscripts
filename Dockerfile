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
VOLUME ["/storage/Handbrake", "/storage/Media_DVD_Movies", "/storage/Media_DVD_Series", "/storage/Media_BD_Movies", "/storage/Media_BD_Series"]

# set entrypoint
CMD ["cron", "-f"]