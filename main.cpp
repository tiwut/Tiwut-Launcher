#include "LauncherWindow.h"
#include <QApplication>

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    LauncherWindow window;
    window.show();
    return app.exec();
}
