#ifndef APPMANAGER_H
#define APPMANAGER_H

#include <QObject>
#include <QNetworkAccessManager>
#include <QPixmap>
#include <QCache>
#include <QList>
#include <QUrl>
#include "appdata.h"

class QNetworkReply;

class AppManager : public QObject {
    Q_OBJECT

public:
    explicit AppManager(QObject *parent = nullptr);

    void loadLibrary();
    QList<AppData> getAllApps() const;
    QList<AppData> getInstalledApps() const;
    bool isAppInstalled(const AppData &app) const;

    void getIcon(const AppData &app);
    void installApp(const AppData &app);
    void uninstallApp(const AppData &app);
    void launchApp(const AppData &app);
    void createShortcut(const AppData &app);

signals:
    void libraryLoaded();
    void iconReady(const QUrl &url, const QPixmap &pixmap);
    void installProgress(int percentage, const QString &status, const QString &info);
    void installFinished(bool success, const QString &message);
    void appStatusChanged();

private slots:
    void onLibraryReplyFinished();
    void onIconReplyFinished();
    void onDownloadProgress(qint64 bytesReceived, qint64 bytesTotal);
    void onDownloadFinished();

private:
    void parseLibrary(const QByteArray &data);
    void extractZip(const QString &zipPath, const QString &extDirPath);

    QNetworkAccessManager *m_networkManager;
    QList<AppData> m_allApps;
    QCache<QString, QPixmap> m_iconCache;

    QNetworkReply *m_downloadReply = nullptr;
    AppData m_currentInstallApp;
};

#endif
