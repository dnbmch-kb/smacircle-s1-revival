cmake_minimum_required(VERSION 3.21)
project(SmacircleQt VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 6.5 REQUIRED COMPONENTS Quick Bluetooth)

qt_standard_project_setup(REQUIRES 6.5)

# Version from the latest git tag (e.g. v0.1.0). Falls back when tags/git absent.
find_package(Git QUIET)
set(APP_VERSION "0.0.0-dev")
if(Git_FOUND)
    execute_process(
        COMMAND ${GIT_EXECUTABLE} describe --tags --always --dirty
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        OUTPUT_VARIABLE _git_desc OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
    if(_git_desc)
        set(APP_VERSION "${_git_desc}")
    endif()
endif()
string(REGEX REPLACE "^v" "" APP_VERSION_NAME "${APP_VERSION}")
set(APP_VERSION_CODE 1)
if(APP_VERSION MATCHES "^v?([0-9]+)\\.([0-9]+)\\.([0-9]+)")
    math(EXPR APP_VERSION_CODE "${CMAKE_MATCH_1}*10000 + ${CMAKE_MATCH_2}*100 + ${CMAKE_MATCH_3}")
endif()
message(STATUS "Smacircle version: ${APP_VERSION} (name=${APP_VERSION_NAME} code=${APP_VERSION_CODE})")

qt_add_executable(SmacircleQt
    main.cpp
    blecontroller.cpp
    blecontroller.h
    protocol.h
)

qt_add_qml_module(SmacircleQt
    URI Smacircle
    VERSION 1.0
    QML_FILES Main.qml
)

# App / window icon (cross-platform, via Qt resource)
qt_add_resources(SmacircleQt "appicon"
    PREFIX "/"
    FILES icon/icon.png
)

# Windows: GUI app (no console window) + exe icon (app.rc -> icon/app.ico)
set_target_properties(SmacircleQt PROPERTIES WIN32_EXECUTABLE ON)
if(WIN32)
    target_sources(SmacircleQt PRIVATE app.rc)
endif()

target_link_libraries(SmacircleQt PRIVATE Qt6::Quick Qt6::Bluetooth)
target_compile_definitions(SmacircleQt PRIVATE APP_VERSION="${APP_VERSION}")

# --- Android packaging (no effect on desktop builds) ---
if(ANDROID)
    set_target_properties(SmacircleQt PROPERTIES
        QT_ANDROID_PACKAGE_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/android"
        QT_ANDROID_TARGET_SDK_VERSION 34
        QT_ANDROID_MIN_SDK_VERSION    28   # Qt 6.10 floor = Android 9.0
        QT_ANDROID_VERSION_NAME       "${APP_VERSION_NAME}"
        QT_ANDROID_VERSION_CODE       ${APP_VERSION_CODE}
    )
endif()
