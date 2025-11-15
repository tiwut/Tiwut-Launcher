#include "mainwindow.h"
#include "appconfig.h"
#include <QApplication>
#include <QDir>

int main(int argc, char *argv[]) {
    QApplication a(argc, argv);

    QDir dir;
    dir.mkpath(AppConfig::APP_DATA_DIR);
    dir.mkpath(AppConfig::ICON_CACHE_DIR);
    dir.mkpath(AppConfig::INSTALL_BASE_PATH);

    MainWindow w;
    w.show();

    return a.exec();
}
