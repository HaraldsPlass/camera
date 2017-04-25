#!/bin/bash
# izveido izvaddatu - LOG datni alpr_install.log
exec > >(tee alpr_install.log)
exec 2>&1
# ieraksta datumu LOG datnē
date
# atjaunija Pi, jo pretējā gadījumā var būt problēmas ar bibliotēku kompilēšanu
sudo apt-get update && sudo apt-get upgrade -y --force-yes
date
# lejupielādē un uzinstalē nepieciešamās bibliotēkas priekš tesseract
date
sudo apt-get install -y --force-yes autoconf build-essential git cmake pkg-config
date
sudo apt-get install -y --force-yes autoconf automake libtool
date
sudo apt-get install -y --force-yes autoconf-archive
date
sudo apt-get install -y --force-yes pkg-config
date
sudo apt-get install -y --force-yes libpng12-dev
date
sudo apt-get install -y --force-yes libjpeg8-dev
date
sudo apt-get install -y --force-yes libjpeg-dev
date
sudo apt-get install -y --force-yes libtiff5-dev
date
sudo apt-get install -y --force-yes zlib1g-dev
date
sudo apt-get install -y --force-yes libjasper-dev
date
sudo apt-get install -y --force-yes libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
date
sudo apt-get install -y --force-yes libxvidcore-dev libx264-dev libgtk2.0-dev libatlas-base-dev
date
sudo apt-get install -y --force-yes gfortran python2.7-dev python3-dev
date
sudo apt-get install -y --force-yes libcurl4-openssl-dev liblog4cplus-1.0-4 liblog4cplus-dev uuid-dev
date
sudo apt-get install -y --force-yes uv4l uv4l-raspicam uv4l-raspicam-extras uv4l-server uv4l-mjpegstream
date
sudo apt-get install -y --force-yes libleptonica-dev

# noklonē openalpr bibliotēkas datnes:
date
cd /home/pi
git clone https://github.com/openalpr/openalpr.git
date
# izveido direktoriju un lejupielādē saistītās bibliotēkas
date
cd openalpr
mkdir libraries
cd libraries

echo "git clone https://github.com/tesseract-ocr/tesseract.git"
date
git clone --depth 1 https://github.com/tesseract-ocr/tesseract.git
date
git clone https://github.com/tesseract-ocr/tessdata.git
date
wget http://www.leptonica.com/source/leptonica-1.74.1.tar.gz
date
wget -O opencv.zip https://github.com/Itseez/opencv/archive/3.1.0.zip
date
wget -O opencv_contrib.zip https://github.com/Itseez/opencv_contrib/archive/3.1.0.zip

# atarhivē leptonica
date
tar -zxvf leptonica-1.74.1.tar.gz
# atarhivē opencv-2.4.9.zip
date
unzip opencv.zip
date
unzip opencv_contrib.zip

# kompilē leptonica:
date
cd leptonica-1.74.1
date
sudo ./configure
date
sudo make -j4
date
sudo make install

# kompilē tesseract:
cd ../tesseract
date
sudo apt-get install -y --force-yes autoconf automake libtool
date
sudo ./autogen.sh
date
sudo apt-get install -y --force-yes autoconf-archive
date
sudo ./configure --enable-debug
LDFLAGS="-L/usr/local/lib" CFLAGS="-I/usr/local/include"
date
sudo make -j4
date
sudo make install
date
sudo ldconfig

# instalē openCV 3 ar Python 2.7
cd /home/pi/openalpr/libraries/
date
wget https://bootstrap.pypa.io/get-pip.py
date
sudo python get-pip.py
date
sudo pip install virtualenv virtualenvwrapper
date
sudo rm -rf ~/.cache/pip
date
echo 'export WORKON_HOME=$HOME/.virtualenvs' >> ~/.profile
echo 'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.profile
date
source ~/.profile
date
mkvirtualenv cv
source ~/.profile
date
workon cv
date
pip install numpy

cd /home/pi/openalpr/libraries/opencv-3.1.0
date
mkdir build
cd build
date
cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local -D INSTALL_C_EXAMPLES=OFF -D INSTALL_PYTHON_EXAMPLES=ON -D OPENCV_EXTRA_MODULES_PATH=/home/pi/openalpr/libraries/opencv_contrib-3.1.0/modules -D BUILD_EXAMPLES=ON ..
date
sudo make -j4
date
sudo make install
date
sudo ldconfig
cd ~/.virtualenvs/cv/lib/python2.7/site-packages/
date
ln -s /usr/local/lib/python2.7/site-packages/cv2.so cv2.so

# kompilē openALPR:
cd /home/pi/openalpr/src

# nano CMakeLists.txt
# pievieno šādas rindas sākumā, kur jau ir SET() apgalvojumi
# SET(OpenCV_DIR "/home/pi/openalpr/libraries/opencv-2.4.11/release")
# SET(Tesseract_DIR "/home/pi/openalpr/libraries/tesseract")
# darma to, izmantojot komandu SED
date
sed -i '11 i SET(Tesseract_DIR "/home/pi/openalpr/libraries/tesseract")' /home/pi/openalpr/src/CMakeLists.txt
sed -i '11 i SET(OpenCV_DIR "~/openalpr/libraries/opencv-3.1.0/build")' /home/pi/openalpr/src/CMakeLists.txt 

date
sudo cmake ./
date
sudo make -j4
date
sudo make install
date
sudo cp -r /usr/local/lib/* /lib

# notestē OpenALPR bibliotēku, izmantojot standartattēlu ar ASV numura zīmi
date
wget http://plates.openalpr.com/ea7the.jpg
date
alpr -c us ea7the.jpg
date
