QT       += core gui widgets network


greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

CONFIG += c++17
DEFINES += QT_DEPRECATED_WARNINGS


TARGET = TiwutAppStoreClient
TEMPLATE = app

HEADERS += \
    mainwindow.h \
    appmanager.h \
    appdata.h \
    appconfig.h \
    appgridviewpage.h \
    detailspage.h \
    appcard.h

SOURCES += \
    main.cpp \
    mainwindow.cpp \
    appmanager.cpp \
    appgridviewpage.cpp \
    detailspage.cpp \
    appcard.cpp \
    appconfig.cpp

FORMS += \
    mainwindow.ui

qnx: target.path = /tmp/$${TARGET}/bin
else: unix:!android: target.path = /opt/$${TARGET}/bin
!isEmpty(target.path): INSTALLS += target

QMAKE_LFLAGS += -static-libgcc -static-libstdc++
