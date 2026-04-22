#ifndef LAUNCHERWINDOW_H
#define LAUNCHERWINDOW_H

#include <QHBoxLayout>
#include <QJsonArray>
#include <QJsonObject>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QMainWindow>
#include <QMap>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QPointer>
#include <QProgressBar>
#include <QPushButton>
#include <QVBoxLayout>

struct NexusApp {
  QString id;
  QString name;
  QString description;
  QString iconUrl;
  QString downloadUrl;
  QString version;
  bool isInstalled = false;
};

class LauncherWindow : public QMainWindow {
  Q_OBJECT

public:
  LauncherWindow(QWidget *parent = nullptr);
  ~LauncherWindow();

private slots:
  void fetchLibrary();
  void onLibraryFetched(QNetworkReply *reply);
  void onAppSelected(QListWidgetItem *item);
  void installSelectedApp();
  void uninstallSelectedApp();
  void launchSelectedApp();
  void openSettings();
  void onSearchTextChanged(const QString &text);
  void onDownloadProgress(qint64 bytesReceived, qint64 bytesTotal);
  void onDownloadFinished();

private:
  void setupUI();
  void updateAppDetailsView();
  QString getAppsDirectory() const;
  QString getInterpreterPath() const;
  void checkInstalledApps();

  QNetworkAccessManager *networkManager;
  QNetworkReply *currentDownload;

  QListWidget *appListWidget;
  QLabel *appNameLabel;
  QLabel *appDescLabel;
  QLabel *appIconLabel;
  QPushButton *installBtn;
  QPushButton *launchBtn;
  QPushButton *uninstallBtn;
  QPushButton *settingsBtn;
  QLineEdit *searchBar;
  QProgressBar *progressBar;

  QMap<QString, NexusApp> apps;
  QString selectedAppId;

  const QString libraryUrl =
      "https://raw.githubusercontent.com/tiwut/"
      "Tiwut-Launcher/refs/heads/main/library-respo.tiwut";
};

#endif
