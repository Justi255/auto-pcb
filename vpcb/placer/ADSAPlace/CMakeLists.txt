cmake_minimum_required(VERSION 3.1)

project(PCBPLACER)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(THREADS_PREFER_PTHREAD_FLAG ON)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -pthread -Ofast -funsafe-math-optimizations -fpermissive -fPIC")
set(CMAKE_CXX_FLAGS_DEBUG "-g -ggdb")

find_package(Boost REQUIRED)

include_directories(${Boost_INCLUDE_DIR})
link_directories(${Boost_LIBRARYDIR})

set(PCBPLACER_HOME ${PROJECT_SOURCE_DIR} )
set(PCBROUTER_HOME ${PROJECT_SOURCE_DIR}/router )
set(KICADPARSER_HOME ${PROJECT_SOURCE_DIR}/database)

add_subdirectory(${KICADPARSER_HOME})
add_subdirectory(${PCBROUTER_HOME})

set (PCBPLACER_SRC  
  placer.cpp
  globalParam.cpp
  readFiles.cpp
  module.cpp
  element.cpp
  linreg.cpp
  )

set (PCBPLACER_HEADER
  placer.hpp
  globalParam.h
  util.h
  element.hpp
  module.hpp
  readFiles.hpp
  pin.hpp
  linreg.h
  )

############################################################
# include directories
############################################################
include_directories(
  ${KICADPARSER_HOME}
  ${PCBROUTER_HOME}
  )

############################################################
# Create a library
############################################################
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${PCBPLACER_HOME}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PCBPLACER_HOME}/lib)

add_library( PCBPLACERlib SHARED
  ${PCBPLACER_SRC}
)

set_target_properties( PCBPLACERlib
  PROPERTIES OUTPUT_NAME "PCBPLACER"
)

############################################################
# Create an executable
############################################################

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PCBPLACER_HOME}/bin)

add_executable( PCBPLACER main.cpp )
add_dependencies( PCBPLACER kicadpcbparserlib pcbrouter)

target_link_libraries( PCBPLACER
  PCBPLACERlib
  kicadpcbparserlib
  pcbrouterlib
  ${Boost_LIBRARIES}
)