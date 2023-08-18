FROM ubuntu:latest

# Create home directory
RUN mkdir /home/MkvScripts

# Copy files
COPY . /home/MkvScripts
WORKDIR /home/MkvScripts

# Update and install dependencies
RUN apt-get update

# Install mkvtoolnix and openssh-server
RUN apt-get install -y mkvtoolnix openssh-server

# Setup OpenSSH Server
RUN mkdir /var/run/sshd
RUN echo 'root:root' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd
EXPOSE 22

# Setup Volume
VOLUME /storage

# set entrypoint
CMD ["/usr/sbin/sshd", "-D"]