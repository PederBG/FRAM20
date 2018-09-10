# FRAM19

### A GIS application for easy access to relevant sensor data from the arctic region
 
####  Download, process and present up to date satellite imagery, and other sensor data, from a specified area.

###### Developed as an internship assignment for Lundin Norway.

#### Note: *This is work in progress*

### Development

###### Note: The project use both python2 and python3. Back end (django) is using python3.6, but the data generating scripts use modules that only supports python <= 2.7.

#### Docker image (recommended)
- Install Docker: https://docs.docker.com/install/

- Get docker image:
  ```sh
  docker pull pederbg/fram19
  ```
  
- Run docker image:
  ```sh
  ./docker/run_docker.sh
  ```

#### Debian/Ubuntu full setup

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

