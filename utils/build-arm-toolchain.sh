#!/bin/bash

BUILD_DIR=arm-toolchain-build

# Construimos e instalamos la toolchain
mkdir -p $BUILD_DIR
cp arm-toolchain-config $BUILD_DIR/.config
cd $BUILD_DIR
../ctng/ct-ng build
cd ..
rm -rf $BUILD_DIR

# Agregamos la toolchain al path
echo 'export PATH=$HOME/x-tools/arm-cortex_a8-linux-gnueabi/bin:$PATH' >> ~/.bashrc

# Finalizamos, avisar al usuario.
echo "La toolchain se instalo exitosamente."
echo "Cierre esta terminal y abra una nueva."

