#ifndef APPDATA_H
#define APPDATA_H

#include <QString>
#include <QUrl>
#include <QMetaType>

struct AppData {
    QString name;
    QUrl downloadUrl;
    QUrl websiteUrl;
    QUrl iconUrl;

    bool operator==(const AppData& other) const {
        return name == other.name;
    }
};

Q_DECLARE_METATYPE(AppData)

#endif
