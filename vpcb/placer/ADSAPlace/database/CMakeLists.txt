cmake_minimum_required(VERSION 3.1)

project(KiCadPcbParser)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(THREADS_PREFER_PTHREAD_FLAG ON)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -fPIC")
set(CMAKE_CXX_FLAGS_DEBUG "-g -ggdb")
set(CMAKE_CXX_FLAGS_RELEASE "-O3")
#find_library(SWIG_EXECUTABLE swig)
#if(NOT SWIG_EXECUTABLE)
#set(SWIG_EXECUTABLE "/bin/swig")
#set(SWIG_EXECUTABLE "/usr/local/bin/swig")
#set(SWIG_EXECUTABLE "swig")
#endif()

#find_package( PythonInterp 2.7 REQUIRED )
#find_package( PythonInterp 3 REQUIRED )
#find_package( PythonLibs 2.7 REQUIRED )
#find_package( PythonLibs 3 REQUIRED )
#find_package(SWIG REQUIRED)
find_package(Boost REQUIRED)

set(KICADPCB_HOME ${PROJECT_SOURCE_DIR} )

set (KICADPCB_SRC 
  kicadPcbDataBase.cpp
  kicadParser.cpp
  shape.cpp
  util.cpp
  )

set (KICADPCB_HEADER
  kicadPcbDataBase.h
  point.h
  net.h
  kicadParser.h
  tree.h
  util.h
  shape.h
  pin.h
  pcbBoost.h
  rule.h
  module.h
  object.h
  )


############################################################
# include directories 
############################################################
include_directories(
    ${Boost_INCLUDE_DIR}
  )

############################################################
# Create a library 
############################################################
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${KICADPCB_HOME}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${KICADPCB_HOME}/lib)

add_library( kicadpcbparserlib STATIC
  ${KICADPCB_SRC}
)

set_target_properties( kicadpcbparserlib 
  PROPERTIES OUTPUT_NAME "kicadpcbparser"
)

############################################################
# Create an executable
############################################################
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${KICADPCB_HOME}/bin)


add_executable( kicadpcbparser main.cpp )
target_link_libraries( kicadpcbparser
  kicadpcbparserlib
  )

