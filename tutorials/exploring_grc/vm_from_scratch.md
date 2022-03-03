## Starting from a Fresh Ubuntu 20 VM

Create an Ubuntu 20.04 LTS Server VM, SSH in, and set up remote desktop either [using these steps](http://go.microsoft.com/fwlink/?LinkId=2116615) or simply run the commands below:

```console
sudo apt-get update
sudo apt-get -y install xfce4
sudo apt-get install xfce4-session
sudo apt-get -y install xrdp
sudo systemctl enable xrdp
echo xfce4-session >~/.xsession
sudo service xrdp restart
```

Once you have a remote desktop connection into the VM, we can install GNU Radio.  In this section we will be installing GNU Radio from source, as it guarantees the best compatibility with 3rd party GNU Radio modules that we will want to use, and lets us use one of the latest versions.

We will first install the prerequisites:

```console
sudo apt-get install -y git cmake g++ libboost-all-dev libgmp-dev swig python3-numpy python3-mako \
  python3-sphinx python3-lxml doxygen libfftw3-dev libsdl1.2-dev libgsl-dev libqwt-qt5-dev libqt5opengl5-dev \
  python3-pyqt5 liblog4cpp5-dev libzmq3-dev python3-yaml python3-click python3-click-plugins python3-zmq \
  python3-scipy python3-gi python3-gi-cairo gir1.2-gtk-3.0 libcodec2-dev libgsm1-dev pybind11-dev \
  python3-matplotlib libsndfile1-dev python3-pip libsoapysdr-dev soapysdr-tools
 
sudo pip install pygccxml pyqtgraph
```

Next we must install VOLK from source.  VOLK stands for Vector-Optimized Library of Kernels and it is designed to help GNU Radio work with the CPU's [SIMD](https://en.wikipedia.org/wiki/SIMD) instruction set. These are very powerful vector operations that can give signal processing a huge boost in performance. 

```console
cd ~
git clone --recursive https://github.com/gnuradio/volk.git
cd volk
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE=/usr/bin/python3 ../
make -j4
sudo make install
sudo ldconfig
```
Now we can install GNU Radio, specifically version 3.9.  Note the first command below is a band aid fix for a bug related to cmake finding boost and looking in the wrong spot.  

```console
sudo ln -s /usr/include /include
cd ~
git clone https://github.com/gnuradio/gnuradio.git
cd gnuradio
git checkout maint-3.9
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE=/usr/bin/python3 ../
make -j4
sudo make install
sudo ldconfig
```

If no errors occurred, you should now have GNU Radio installed!

### Installing Azure SDR Blocks from Source

Next let's install the gr-azure-software-radio out-of-tree module (OOT) so we can work with Azure.  A dependency is the Azure CLI which can be installed with:
```console
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

Next lets clone our azure-software-radio repo and install all dependencies with:
```console
sudo apt-get install -y cmake python3-pip liborc-dev doxygen
cd ~
git clone https://github.com/microsoft/azure-software-radio.git
cd azure-software-radio/
cd gr-azure-software-radio/
pip install pytest pybind11
pip install -r python/requirements.txt
```

Now to build and install the OOT:
```console
mkdir build
cd build
cmake ..
make -j4
sudo make install
sudo ldconfig
```

At this point you have GNU Radio and the Azure SDR blocks installed, **you can skip to the section [Running GNU Radio](README.md#running-gnu-radio).**
