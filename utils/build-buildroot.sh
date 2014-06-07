#!/bin/bash

BR=buildroot-2014.02
wget http://buildroot.org/downloads/$BR.tar.gz -P$HOME/Downloads/src
tar -C . -xvzf $HOME/Downloads/src/$BR.tar.gz

cd $BR

# Aplicamos unos parches para instalar paquetes de Python.
patch -p1 < ../buildroot-patches/update-python-setuptools-2.1.patch
patch -p1 < ../buildroot-patches/add-python-packages.patch
patch -p1 < ../buildroot-patches/add-python-autobahn.patch
patch -p1 < ../buildroot-patches/add-python-cffi.patch
patch -p1 < ../buildroot-patches/i2c-tools-with-python-smbus.patch
patch -p1 < ../buildroot-patches/use-coreutils-mktemp.patch

# Copiamos el archivo de configuracion.
cp ../buildroot-config .config

cd ..

# Finalizamos.
mv $BR buildroot
echo "Se creo el directorio \"buildroot\"."
