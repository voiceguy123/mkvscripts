FROM ubuntu:latest

# Create home directory
RUN mkdir /home/MkvScripts

# Copy files
COPY . /home/MkvScripts
WORKDIR /home/MkvScripts

# Update and install dependencies
RUN apt-get update

# Install mkvtoolnix
RUN apt-get install -y mkvtoolnix

# set entrypoint
CMD ["bash"]