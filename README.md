# FRAM-2019

### Website / GIS application used for the FRAM-2019 expedition, due to start spring 2019.
#### Visit at: www.fram2019.com (still in dev)

####  Using python to download and process up to date satellite imagery, and other sensor data, following specified locations in the Artic Ocean. Presenting this in a full-stack Django application with GeoServer and OpenLayers. Application deployed using NGINX and Gunicorn. All configurations and dependencies are handled by Docker.

###### Developed as an internship assignment for Lundin Norway. Source code published with their consent.
![Github](https://preview.ibb.co/jC8s8A/fram.png "Preview")

### Development
##### Note: *not updated to newest changes*

#### Use docker image (highly recommended)

- Fork the project and clone it in your own project folder:
  ```sh
  git clone https://github.com/PederBG/FRAM19.git
  ```

- Install Docker: https://docs.docker.com/install/

- Get docker image:
  ```sh
  docker pull pederbg/fram19
  ```

- Run docker image:
  ```sh
  cd FRAM19/docker
   sudo ./run_docker.sh
  ```
The docker file will automatically start django and geoserver in two tmux sessions.

- Navigate to `http://localhost:8000/`

To display sensor data in the application the overlays needs to be generated. This is done using scripts/main.py. Type `./scripts/main.py --help` to see the options. However to see the overlays in the application a refrence have to be added in the database.

###### Note that this process may take a lot of time and bandwidth depending on your download speed and available RAM. Also note that some images can take up to 5GB of disk space.

- Run this command to download overlays for a given day (default is June 22, 2018) and add refrence to the database:
   ```sh
  python3 manage.py getsensordata
  ```
<br><br>


#### Debian/Ubuntu full setup (not recommended)
###### Note: The project use both python2 and python3. The django app is using python3.6, but the data generating scripts need packages that only supports python <= 2.7.

- Fork the project and clone it in your own project folder:
  ```sh
  git clone https://github.com/PederBG/FRAM19.git
  ```
- Make sure you have both python2 and python3 installed.

- Install pip for both python versions if you do not have it already:
  ```sh
  apt-get install python-pip
  apt-get install python3-pip
  ```
- Ensure pip, setuptools, and wheel are up to date
  ```sh
  pip2 install --upgrade pip setuptools wheel
  pip3 install --upgrade pip setuptools wheel
  ```
- Get Java JDK:
  ```sh
  apt-get install default-jdk
  ```
- Download and install latest geoserver version:
  - Select Platform Independent Binary at http://geoserver.org/release/stable/
  - Unpack the archive where you want geoserver to be located (/usr/share/geoserver)
  - Setup geoserver on your system:
      ```sh
      echo "export GEOSERVER_HOME=/path/to/geoserver" >> ~/.profile
      . ~/.profile
      chown -R USER_NAME /path/to/geoserver/
      echo "geoserver='sh /path/to/geoserver/bin/startup.sh'" >> ~/.bashrc && source ~/.bashrc
      ```
  - Test geoserver by running `geoserver` and navigate to `http://localhost:8080/geoserver`
- Install all python packages needed:

  Python3:
  - Django: `pip3 install django`

  Python2:
  - NumPy: `pip2 install numpy`
  - SciPy: `pip2 install scipy`
  - sentinelsat: `pip2 install sentinelsat`
  - matplotlib: `apt-get install python-matplotlib`

- Install Geospatial Data Abstraction Library (GDAL):
    ```sh
  add-apt-repository -y ppa:ubuntugis/ppa
  apt update
  apt upgrade
  apt install gdal-bin python-gdal
  ```

- Install netCDF4 package:
  - First install dependencies:
    - C compiler: `apt-get install build-essential`
    - Cython C-Extensions for Python: `pip2 install Cython`
  - Install HDF5:
  ```sh
  apt-get install libhdf5-serial-dev netcdf-bin libnetcdf-dev
  pip2 install h5py
  ```
    - Install netCDF4: `pip2 install netcdf4`


#### Test project

- Run this, if no errors occur setup was successful:
  ```sh
  cd path/to/project
  scripts/getdata.py --test
  python3 manage.py runserver
  ```
