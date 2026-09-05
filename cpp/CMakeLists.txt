cmake_minimum_required(VERSION 3.10)
project(yolo26_dual_cpp CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_CXX_FLAGS_RELEASE "-O3")
  set(CMAKE_BUILD_TYPE Release)
endif()

# ----------------------------------------------------------------------------
# Dependencies
# ----------------------------------------------------------------------------
# OpenCV (core/imgproc/imgcodecs/videoio/video) shipped with the RDK image.
find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs videoio video)

# X5 Hobot DNN runtime (libdnn.so), libdrm for KMS, and libyuv for scaling.
set(HOBOT_LIB /usr/lib)

enable_testing()

# ----------------------------------------------------------------------------
# ByteTrack (native C++ person tracker)
# ----------------------------------------------------------------------------
add_library(byte_tracker STATIC
  src/tracking/byte_tracker.cpp)
target_include_directories(byte_tracker PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/src
  ${OpenCV_INCLUDE_DIRS})
target_link_libraries(byte_tracker PUBLIC ${OpenCV_LIBS})

add_executable(test_byte_tracker tests/test_byte_tracker.cpp)
target_link_libraries(test_byte_tracker PRIVATE byte_tracker)
add_test(NAME byte_tracker COMMAND test_byte_tracker)

# ----------------------------------------------------------------------------
# Browser overlay (track boxes / labels / depth focus marker)
# ----------------------------------------------------------------------------
add_library(browser_overlay STATIC src/ui/browser_overlay.cpp)
target_include_directories(browser_overlay PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/src
  ${OpenCV_INCLUDE_DIRS})
target_link_libraries(browser_overlay PUBLIC byte_tracker ${OpenCV_LIBS})

add_executable(test_browser_overlay tests/test_browser_overlay.cpp)
target_link_libraries(test_browser_overlay PRIVATE browser_overlay)
add_test(NAME browser_overlay COMMAND test_browser_overlay)

# ----------------------------------------------------------------------------
# System metrics (CPU / memory from /proc, BPU from sysfs)
# ----------------------------------------------------------------------------
add_library(system_metrics STATIC src/system_metrics.cpp)
target_include_directories(system_metrics PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_link_libraries(system_metrics PUBLIC pthread)

add_executable(test_system_metrics tests/test_system_metrics.cpp)
target_link_libraries(test_system_metrics PRIVATE system_metrics)
add_test(NAME system_metrics COMMAND test_system_metrics)

# ----------------------------------------------------------------------------
# Main demo binary
# ----------------------------------------------------------------------------
add_executable(yolo26_dual src/main.cpp)
target_include_directories(yolo26_dual PRIVATE
  /usr/include
  /usr/include/libdrm
  ${OpenCV_INCLUDE_DIRS})
target_link_libraries(yolo26_dual
  ${OpenCV_LIBS}
  pthread
  ${HOBOT_LIB}/libdnn.so
  drm yuv)
target_link_libraries(yolo26_dual byte_tracker browser_overlay system_metrics)
# Keep the Horizon runtime libs resolvable at runtime.
set_target_properties(yolo26_dual PROPERTIES
  BUILD_RPATH "${HOBOT_LIB}"
  INSTALL_RPATH "${HOBOT_LIB}")

# Deploy the complete project using scripts/install.sh; the S100P CPack layout is not used.
