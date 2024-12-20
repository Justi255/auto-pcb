set(OP_NAME pinrudy)

set(TARGET_NAME ${OP_NAME})

set(INCLUDE_DIRS 
  ${CMAKE_CURRENT_SOURCE_DIR}/..
  )

set(LINK_LIBS utility_cxx
  OpenMP::OpenMP_CXX
  )

add_pytorch_extension(${TARGET_NAME}_cpp 
  src/pinrudy.cpp
  EXTRA_INCLUDE_DIRS ${INCLUDE_DIRS}
  EXTRA_LINK_LIBRARIES ${LINK_LIBS})

install(TARGETS 
  ${TARGET_NAME}_cpp 
  DESTINATION ops/${OP_NAME})

if(TORCH_ENABLE_CUDA)
add_pytorch_extension(${TARGET_NAME}_cuda 
  src/pinrudy_cuda.cpp
  src/pinrudy_cuda_kernel.cu
  EXTRA_INCLUDE_DIRS ${INCLUDE_DIRS}
  EXTRA_LINK_LIBRARIES ${LINK_LIBS})

install(TARGETS 
  ${TARGET_NAME}_cuda 
  DESTINATION ops/${OP_NAME})
endif(TORCH_ENABLE_CUDA)
