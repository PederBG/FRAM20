FROM ubuntu:16.04

ENV DEBIAN_FRONTEND noninteractive
ENV APT_QUIET "apt-get -yqq -o=Dpkg::Use-Pty=0"

RUN $APT_QUIET update && \
    $APT_QUIET install --no-install-recommends apt-utils && \
    $APT_QUIET upgrade && \
    $APT_QUIET install  build-essential vim tmux htop iputils-ping unzip python-pip python3 python3-pip wget

# JAVA
RUN $APT_QUIET install default-jdk

# GEOSERVER
RUN wget https://sourceforge.net/projects/geoserver/files/GeoServer/2.12.5/geoserver-2.12.5-bin.zip && \
    unzip geoserver-2.12.5-bin.zip && \
    mkdir -p /usr/share && \
    mv geoserver-2.12.5/ /usr/share && \
    rm -f geoserver-2.12.5-bin.zip


RUN python2 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install django whitenoise gunicorn django-mailbox && \
    python2 -m pip install numpy scipy sentinelsat gsconfig pandas && \
    $APT_QUIET install python-matplotlib

# GDAL
RUN $APT_QUIET install software-properties-common
RUN add-apt-repository -y ppa:ubuntugis/ppa && \
    $APT_QUIET update  && \
    $APT_QUIET upgrade && \
    $APT_QUIET install gdal-bin python-gdal

# NGINX
RUN $APT_QUIET install nginx

# CERTBOT (FOR SSL CERTIFICATE)
RUN $APT_QUIET update && \
    $APT_QUIET install software-properties-common
RUN add-apt-repository -y universe && \
    add-apt-repository ppa:certbot/certbot
RUN $APT_QUIET update && \
    $APT_QUIET install certbot python-certbot-nginx

# Cython
RUN python2 -m pip install Cython

# HDF5
RUN $APT_QUIET install libhdf5-serial-dev netcdf-bin libnetcdf-dev && \
    python2 -m pip install h5py

# netCDF4
RUN python2 -m pip install netcdf4

# Extra setup
RUN mkdir /root/logs && touch /root/logs/cron.log /root/logs/access.log /root/logs/info.log

RUN rm /etc/localtime && ln -s /usr/share/zoneinfo/Europe/Oslo /etc/localtime

RUN service cron start

#prod (commented out - configure manually)
#ENTRYPOINT  /bin/bash -c 'cp /root/fram19/nginx.conf.copy /etc/nginx/sites-enabled/nginx.conf && rm /etc/nginx/sites-enabled/default && /etc/init.d/nginx restart && tmux new-session -d -s "django" "cd /root/fram19 && python3 manage.py makemigrations && python3 manage.py migrate && python3 manage.py collectstatic --noinput &&  gunicorn --access-logfile /root/logs/access.log --workers 3 -b :8000 v2fram.wsgi:application" && tmux new-session -d -s "geoserver" "cd /root/fram19 && GEOSERVER_HOME=usr/share/geoserver-2.12.5 /usr/share/geoserver-2.12.5/bin/startup.sh" && cd /root/fram19 && /bin/bash'

#dev
ENTRYPOINT  /bin/bash -c \
    'tmux new-session -d -s "django" \
        "cd /root/fram19 && python3 manage.py makemigrations && \
        python3 manage.py migrate && python3 manage.py collectstatic --noinput && \
        python3 manage.py runserver" && \
    tmux new-session -d -s "geoserver" \
        "cd /root/fram19 && GEOSERVER_HOME=/usr/share/geoserver-2.12.5 \
        /usr/share/geoserver-2.12.5/bin/startup.sh" && cd /root/fram19 && \
    /bin/bash'
