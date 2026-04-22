cmake_minimum_required(VERSION 3.16)
project(NexusLauncher VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 COMPONENTS Core Gui Widgets Network REQUIRED)

add_executable(NexusLauncher
    main.cpp
    LauncherWindow.cpp
    LauncherWindow.h
)

target_link_libraries(NexusLauncher PRIVATE Qt6::Core Qt6::Gui Qt6::Widgets Qt6::Network)
