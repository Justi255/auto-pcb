set(OP_NAME logsumexp_wirelength)

set(TARGET_NAME ${OP_NAME})

set(INCLUDE_DIRS 
  ${CMAKE_CURRENT_SOURCE_DIR}/..
  )

set(LINK_LIBS utility_cxx
  OpenMP::OpenMP_CXX
  )

add_pytorch_extension(${TARGET_NAME}_cpp_merged 
  src/logsumexp_wirelength_merged.cpp
  EXTRA_INCLUDE_DIRS ${INCLUDE_DIRS}
  EXTRA_LINK_LIBRARIES ${LINK_LIBS})

install(TARGETS 
  ${TARGET_NAME}_cpp_merged 
  DESTINATION ops/${OP_NAME})

if(TORCH_ENABLE_CUDA)
add_pytorch_extension(${TARGET_NAME}_cuda_merged
  src/logsumexp_wirelength_cuda_merged.cpp
  src/logsumexp_wirelength_cuda_merged_kernel.cu
  EXTRA_INCLUDE_DIRS ${INCLUDE_DIRS}
  EXTRA_LINK_LIBRARIES integrate_net_weights_cuda ${LINK_LIBS})

add_pytorch_extension(${TARGET_NAME}_cuda_atomic 
  src/logsumexp_wirelength_cuda_atomic.cpp
  src/logsumexp_wirelength_cuda_atomic_kernel.cu 
  EXTRA_INCLUDE_DIRS ${INCLUDE_DIRS}
  EXTRA_LINK_LIBRARIES integrate_net_weights_cuda ${LINK_LIBS})

install(TARGETS 
  ${TARGET_NAME}_cuda_merged 
  ${TARGET_NAME}_cuda_atomic
  DESTINATION ops/${OP_NAME})
endif(TORCH_ENABLE_CUDA)
