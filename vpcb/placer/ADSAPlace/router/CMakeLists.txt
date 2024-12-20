cmake_minimum_required(VERSION 3.1)

project(PcbRouter)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -fPIC")
set(CMAKE_CXX_FLAGS_DEBUG "-g -ggdb")
set(CMAKE_CXX_FLAGS_RELEASE "-O3")

if(NOT CMAKE_BUILD_TYPE)
    # default to Release build for GCC builds
    set(CMAKE_BUILD_TYPE Release CACHE STRING
        "Choose the type of build, options are: None(CMAKE_CXX_FLAGS or CMAKE_C_FLAGS used) Debug Release."
        FORCE)
endif()

set(PCBROUTER_HOME ${PROJECT_SOURCE_DIR} )
set(KICADPCB_HOME
  ${PROJECT_SOURCE_DIR}/database
)

find_package(Boost REQUIRED)


add_subdirectory(${KICADPCB_HOME})

set (PCBROUTER_SRC 
  BoardGrid.cpp
  GridBasedRouter.cpp
  GridNetclass.cpp
  GridPath.cpp
  MultipinRoute.cpp
  PostProcessing.cpp
  GridDiffPairNet.cpp
  DesignRuleChecker.cpp
  globalParam.cpp
  frTime.cpp
  frTime_helper.cpp
  )

set (PCBROUTER_HEADER
  BoardGrid.h
  GridBasedRouter.h
  PcbRouterBoost.h
  GridNetclass.h
  GridDiffPairNetclass.h
  GridDiffPairNet.h
  GridCell.h
  GridPin.h
  GridPath.h
  MultipinRoute.h
  PostProcessing.h
  IncrementalSearchGrids.h
  Location.h
  DesignRuleChecker.h
  globalParam_router.h
  frTime.h
  util_router.h
  )


############################################################
# include directories 
############################################################
include_directories(
  ${Boost_INCLUDE_DIR}
  ${KICADPCB_HOME}
  )

############################################################
# Create a library 
############################################################
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${PCBROUTER_HOME}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PCBROUTER_HOME}/lib)

add_library( pcbrouterlib STATIC
  ${PCBROUTER_SRC}
)

set_target_properties( pcbrouterlib 
  PROPERTIES OUTPUT_NAME "pcbrouter"
)

############################################################
# Create an executable
############################################################


set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PCBROUTER_HOME}/bin)

add_executable( pcbrouter main.cpp )

add_dependencies( pcbrouter kicadpcbparserlib1 )

target_link_libraries( pcbrouter
  pcbrouterlib
  kicadpcbparserlib1
)

############################################################
# Install  
############################################################

install(FILES ${PCBROUTER_HEADER} DESTINATION include)
install(TARGETS pcbrouter DESTINATION bin)
install(TARGETS pcbrouterlib DESTINATION lib)
