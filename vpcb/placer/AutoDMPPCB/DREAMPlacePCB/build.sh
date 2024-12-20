#!/bin/bash

if [ ! -d "build" ]; then
  mkdir build
fi

cd build

cmake ..

echo "CMake finished"

make -j8

echo "Make finished"

make install -j8

echo "DREAMPlacePCB installed successfully!"