#include "appmanager.h"
#include "appconfig.h"
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QDir>
#include <QProcess>
#include <QMessageBox>
#include <QFile>
#include <QStandardPaths>
#include <QFileInfo>
#include <QApplication>
#include <QDesktopServices>

AppManager::AppManager(QObject *parent)
    : QObject(parent), m_networkManager(new QNetworkAccessManager(this)) {
    m_iconCache.setMaxCost(1024 * 10); // 10 MB cache
}

void AppManager::loadLibrary() {
    QNetworkRequest request(AppConfig::LIBRARY_URL);
    QNetworkReply *reply = m_networkManager->get(request);
    connect(reply, &QNetworkReply::finished, this, &AppManager::onLibraryReplyFinished);
}

QList<AppData> AppManager::getAllApps() const { return m_allApps; }

QList<AppData> AppManager::getInstalledApps() const {
    QList<AppData> installed;
    for (const auto &app : m_allApps) {
        if (isAppInstalled(app)) {
            installed.append(app);
        }
    }
    return installed;
}

bool AppManager::isAppInstalled(const AppData &app) const {
    return QDir(AppConfig::INSTALL_BASE_PATH + "/" + app.name).exists();
}


void AppManager::getIcon(const AppData &app) {
    if (app.iconUrl.isEmpty()) return;

    if (m_iconCache.contains(app.iconUrl.toString())) {
        emit iconReady(app.iconUrl, *m_iconCache.object(app.iconUrl.toString()));
        return;
    }

    QString cacheFileName = QDir(AppConfig::ICON_CACHE_DIR).filePath(app.iconUrl.fileName());
    if (QFile::exists(cacheFileName)) {
        QPixmap pixmap;
        if (pixmap.load(cacheFileName)) {
            m_iconCache.insert(app.iconUrl.toString(), new QPixmap(pixmap));
            emit iconReady(app.iconUrl, pixmap);
            return;
        }
    }

    QNetworkRequest request(app.iconUrl);
    QNetworkReply *reply = m_networkManager->get(request);
    connect(reply, &QNetworkReply::finished, this, &AppManager::onIconReplyFinished);
}

void AppManager::installApp(const AppData &app) {
    m_currentInstallApp = app;
    QString appDir = AppConfig::INSTALL_BASE_PATH + "/" + app.name;
    QDir().mkpath(appDir);

    QNetworkRequest request(app.downloadUrl);
    m_downloadReply = m_networkManager->get(request);

    connect(m_downloadReply, &QNetworkReply::downloadProgress, this, &AppManager::onDownloadProgress);
    connect(m_downloadReply, &QNetworkReply::finished, this, &AppManager::onDownloadFinished);

    emit installProgress(0, "Connecting...", "");
}

void AppManager::uninstallApp(const AppData &app) {
    if (QMessageBox::question(nullptr, "Confirm", "Uninstall " + app.name + "?", QMessageBox::Yes | QMessageBox::No) == QMessageBox::Yes) {
        QString appDir = AppConfig::INSTALL_BASE_PATH + "/" + app.name;
        if (QDir(appDir).removeRecursively()) {
            QMessageBox::information(nullptr, "Success", app.name + " was uninstalled.");
            emit appStatusChanged();
        } else {
            QMessageBox::critical(nullptr, "Error", "Failed to uninstall: Could not remove directory.");
        }
    }
}

void AppManager::launchApp(const AppData &app) {
    QString exePath = AppConfig::INSTALL_BASE_PATH + "/" + app.name + "/main.exe";
    if (!QFile::exists(exePath)) {
        QMessageBox::critical(nullptr, "Error", "'main.exe' not found!");
        return;
    }
    QString workingDir = QFileInfo(exePath).absolutePath();
    QProcess::startDetached("\"" + exePath + "\"", QStringList(), workingDir);
}

void AppManager::createShortcut(const AppData &app) {
    QString targetPath = QDir::toNativeSeparators(AppConfig::INSTALL_BASE_PATH + "/" + app.name + "/main.exe");
    if (!QFile::exists(targetPath)) {
        QMessageBox::critical(nullptr, "Error", "Cannot create shortcut: 'main.exe' not found.");
        return;
    }

    QString desktopPath = QStandardPaths::writableLocation(QStandardPaths::DesktopLocation);
    QString linkPath = QDir::toNativeSeparators(desktopPath + "/" + app.name + ".lnk");

    if (QFile::link(targetPath, linkPath)) {
        QMessageBox::information(nullptr, "Success", "Shortcut for " + app.name + " created on your Desktop.");
    } else {
        QMessageBox::critical(nullptr, "Error", "Could not create shortcut. Trying fallback method...");
    }
}

void AppManager::onLibraryReplyFinished() {
    QNetworkReply *reply = qobject_cast<QNetworkReply*>(sender());
    if (reply->error() == QNetworkReply::NoError) {
        parseLibrary(reply->readAll());
        emit libraryLoaded();
    } else {
        QMessageBox::critical(nullptr, "Network Error", "Could not load app library:\n" + reply->errorString());
        qApp->quit();
    }
    reply->deleteLater();
}

void AppManager::parseLibrary(const QByteArray &data) {
    m_allApps.clear();
    for (const QString &line : QString(data).split('\n', Qt::SkipEmptyParts)) {
        QStringList parts = line.trimmed().split(';');
        if (parts.length() >= 3) {
            AppData app;
            app.name = parts[0];
            app.downloadUrl = QUrl(parts[1]);
            app.websiteUrl = QUrl(parts[2]);
            if (parts.length() >= 4) app.iconUrl = QUrl(parts[3]);
            m_allApps.append(app);
        }
    }
}

void AppManager::onIconReplyFinished() {
    QNetworkReply *reply = qobject_cast<QNetworkReply*>(sender());
    QUrl url = reply->request().url();
    if (reply->error() == QNetworkReply::NoError) {
        QPixmap pixmap;
        pixmap.loadFromData(reply->readAll());
        if (!pixmap.isNull()) {
            m_iconCache.insert(url.toString(), new QPixmap(pixmap));
            QString cacheFileName = QDir(AppConfig::ICON_CACHE_DIR).filePath(url.fileName());
            pixmap.save(cacheFileName);
            emit iconReady(url, pixmap);
        }
    }
    reply->deleteLater();
}

void AppManager::onDownloadProgress(qint64 bytesReceived, qint64 bytesTotal) {
    if (bytesTotal > 0) {
        int percentage = (static_cast<double>(bytesReceived) / bytesTotal) * 100;
        QString info = QString("%1 / %2").arg(AppConfig::formatBytes(bytesReceived)).arg(AppConfig::formatBytes(bytesTotal));
        emit installProgress(percentage, "Downloading " + m_currentInstallApp.name + "...", info);
    }
}

void AppManager::onDownloadFinished() {
    if (m_downloadReply->error() == QNetworkReply::NoError) {
        QString appDir = AppConfig::INSTALL_BASE_PATH + "/" + m_currentInstallApp.name;
        QString zipPath = appDir + "/app.zip";
        QFile file(zipPath);
        if (file.open(QIODevice::WriteOnly)) {
            file.write(m_downloadReply->readAll());
            file.close();
            emit installProgress(100, "Extracting files...", "");
            extractZip(zipPath, appDir);
            QFile::remove(zipPath);
            emit installFinished(true, m_currentInstallApp.name + " was installed successfully.");
            emit appStatusChanged();
        } else {
            emit installFinished(false, "Failed to save downloaded file.");
        }
    } else {
        emit installFinished(false, "Download failed: " + m_downloadReply->errorString());
    }
    m_downloadReply->deleteLater();
    m_downloadReply = nullptr;
}

void AppManager::extractZip(const QString &zipPath, const QString &extDirPath) {
    QProcess process;
    process.setProgram("tar");
    process.setArguments({"-xf", QDir::toNativeSeparators(zipPath), "-C", QDir::toNativeSeparators(extDirPath)});
    process.start();
    process.waitForFinished(-1);
}
