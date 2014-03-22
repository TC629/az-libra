#!/bin/bash

CTNG=crosstool-ng-1.19.0
wget http://crosstool-ng.org/download/crosstool-ng/$CTNG.tar.bz2 -P$HOME/Downloads/src
tar -C . -xvjf $HOME/Downloads/src/$CTNG.tar.bz2
cd $CTNG
./configure
make
cd ..
mv $CTNG ctng
