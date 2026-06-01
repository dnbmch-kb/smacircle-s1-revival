cmake_minimum_required(VERSION 3.21)
project(SmacircleQt VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 6.5 REQUIRED COMPONENTS Quick Bluetooth)

qt_standard_project_setup(REQUIRES 6.5)

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

# Windows: GUI app (no console window) for release.
set_target_properties(SmacircleQt PROPERTIES WIN32_EXECUTABLE ON)

target_link_libraries(SmacircleQt PRIVATE Qt6::Quick Qt6::Bluetooth)

# --- Android packaging (no effect on desktop builds) ---
if(ANDROID)
    set_target_properties(SmacircleQt PROPERTIES
        QT_ANDROID_PACKAGE_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/android"
        QT_ANDROID_TARGET_SDK_VERSION 34
        QT_ANDROID_MIN_SDK_VERSION    28   # Qt 6.10 floor = Android 9.0
        QT_ANDROID_VERSION_NAME       "1.0"
        QT_ANDROID_VERSION_CODE       1
    )
endif()
