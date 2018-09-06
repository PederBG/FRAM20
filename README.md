# FRAM19

### A GIS application for easy access to relevant sensor data from the arctic region
 
####  Download, process and present up to date satellite imagery, and other sensor data, from a specified area.

##### Sensor gathering and processing is written with python. Back end is built with Django while front end uses pure javascript/jQuery, but this is likely to change.

###### Developed as an internship assignment for Lundin Norway.

#### Note: *This is work in progress*

### Development

###### Note: The project use both python2 and python3. Back end (django) is using python3.6, but the data generating scripts use modules that only supports python <= 2.7.

#### Debian / Ubuntu setup

- Fork the project and clone it in your own project folder:
```sh
git clone https://github.com/PederBG/FRAM19.git
```
- Download and install latest geoserver version:
  - Select Platform Independent Binary at http://geoserver.org/release/stable/
  - Unpack the archive where you want geoserver to be located (/usr/share/geoserver)
  - Setup geoserver on your system:
      ```sh
      echo "export GEOSERVER_HOME=/path/to/geoserver" >> ~/.profile
      . ~/.profile
      sudo chown -R USER_NAME /path/to/geoserver/
      echo "geoserver='sh /path/to/geoserver/bin/startup.sh'" >> ~/.bashrc && source ~/.bashrc
      ```
  - Test geoserver by running `geoserver` and navigate to `http://localhost:8080/geoserver`
- Install all python packages needed:
  - Ensure pip, setuptools, and wheel are up to date
    ```sh
    python2.7 -m pip install --upgrade pip setuptools wheel
    python3.6 -m pip install --upgrade pip setuptools wheel
    ```
  Python3.6:
  - Django: `python3.6 -m pip install django`

  Python2.7:
  - NumPy: `python2.7 -m pip install numpy`
  - SciPy: `python2.7 -m pip install scipy`
  - sentinelsat: `python2.7 -m pip install sentinelsat`
  - matplotlib: `sudo apt-get install python-matplotlib`
  
- Install Geospatial Data Abstraction Library (GDAL):
    ```sh
  sudo add-apt-repository -y ppa:ubuntugis/ppa
  sudo apt update 
  sudo apt upgrade
  sudo apt install gdal-bin python-gdal
  ```


- Install netCDF4 package:
  - First install dependencies:
    - C compiler: `sudo apt-get install build-essential`
    - Cython C-Extensions for Python: `python2.7 -m pip install Cython`
  - Install HDF5:
  ```sh
  sudo apt-get install libhdf5-serial-dev netcdf-bin libnetcdf-dev
  python2.7 -m pip install h5py
  ```
    - Install netCDF4: `python2.7 -m pip install netcdf4`

#### Test project

- Run this, if no errors occur setup was successful:
  ```sh
  cd path/to/project
  python2.7 scripts/getdata.py --test
  python3.6 manage.py runserver
  ```

