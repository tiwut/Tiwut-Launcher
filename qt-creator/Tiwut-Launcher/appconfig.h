
#ifndef APPCONFIG_H
#define APPCONFIG_H

#include <QString>
#include <QColor>
#include <QFont>
#include <QStandardPaths>
#include <cmath>

namespace AppConfig {

extern const QString APP_DATA_DIR;
extern const QString ICON_CACHE_DIR;
extern const QString INSTALL_SUBDIR;
extern const QString INSTALL_BASE_PATH;

extern const QString LIBRARY_URL;

extern const QColor Background;
extern const QColor Primary;
extern const QColor Secondary;
extern const QColor Accent;
extern const QColor AccentHover;
extern const QColor Text;
extern const QColor TextSecondary;

extern const QFont FontLargeTitle;
extern const QFont FontTitle;
extern const QFont FontBody;
extern const QFont FontBodyBold;
extern const QFont FontNav;

inline QString formatBytes(qint64 bytes) {
    if (bytes <= 0) return "0 B";
    const char* sizes[] = { "B", "KB", "MB", "GB", "TB" };
    int i = static_cast<int>(floor(log(bytes) / log(1024)));
    if (i < 0 || i >= 5) i = 0;
    double s = round(bytes / pow(1024, i) * 100) / 100;
    return QString("%1 %2").arg(s).arg(sizes[i]);
}
}

#endif
