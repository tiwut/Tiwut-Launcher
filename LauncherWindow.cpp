#include "LauncherWindow.h"
#include <QCoreApplication>
#include <QDebug>
#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QMessageBox>
#include <QPixmap>
#include <QProcess>
#include <QStandardPaths>
#include <QTabWidget>

LauncherWindow::LauncherWindow(QWidget *parent)
    : QMainWindow(parent), networkManager(new QNetworkAccessManager(this)),
      currentDownload(nullptr) {
  setupUI();
  checkInstalledApps();
  fetchLibrary();
}

LauncherWindow::~LauncherWindow() {}

void LauncherWindow::setupUI() {
  setWindowTitle("Tiwut Launcher");
  resize(1000, 700);

  setStyleSheet(R"(
        QMainWindow { background-color: #0f0f13; }
        QLabel { color: #128a12; }
        QListWidget { 
            background-color: rgba(30, 30, 35, 0.8); 
            color: #0060a8; 
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 8px;
            font-size: 15px;
        }
        QListWidget::item { padding: 12px; border-radius: 8px; }
        QListWidget::item:selected { background-color: rgba(60, 60, 70, 0.9); }
        QListWidget::item:hover { background-color: rgba(50, 50, 60, 0.5); }
        QPushButton {
            background-color: #0078D4;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 15px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #1084ea; }
        QPushButton:pressed { background-color: #0060a8; }
        QPushButton:disabled { background-color: #333333; color: #777777; }
        QPushButton#LaunchBtn { background-color: #107c10; }
        QPushButton#LaunchBtn:hover { background-color: #128a12; }
        QPushButton#UninstallBtn { background-color: #d13438; }
        QPushButton#UninstallBtn:hover { background-color: #e3383d; }
        QProgressBar {
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            text-align: center;
            color: white;
            background-color: rgba(30, 30, 35, 0.8);
        }
        QProgressBar::chunk { background-color: #0078D4; border-radius: 8px; }
    )");

  QWidget *centralWidget = new QWidget(this);
  setCentralWidget(centralWidget);

  QHBoxLayout *mainLayout = new QHBoxLayout(centralWidget);
  mainLayout->setContentsMargins(20, 20, 20, 20);
  mainLayout->setSpacing(25);

  QVBoxLayout *leftLayout = new QVBoxLayout();
  QLabel *libraryLabel = new QLabel("<h2>Library</h2>");

  searchBar = new QLineEdit();
  searchBar->setPlaceholderText("Search apps...");
  searchBar->setStyleSheet(
      "background-color: rgba(30,30,35,0.8); color: white; border: 1px solid "
      "rgba(255,255,255,0.1); border-radius: 8px; padding: 8px; font-size: "
      "14px;");
  connect(searchBar, &QLineEdit::textChanged, this,
          &LauncherWindow::onSearchTextChanged);

  appListWidget = new QListWidget();
  connect(appListWidget, &QListWidget::itemClicked, this,
          &LauncherWindow::onAppSelected);

  settingsBtn = new QPushButton("Settings");
  settingsBtn->setStyleSheet("background-color: rgba(60,60,70,0.8);");
  connect(settingsBtn, &QPushButton::clicked, this,
          &LauncherWindow::openSettings);

  leftLayout->addWidget(libraryLabel);
  leftLayout->addWidget(searchBar);
  leftLayout->addWidget(appListWidget);
  leftLayout->addWidget(settingsBtn);

  QVBoxLayout *rightLayout = new QVBoxLayout();
  rightLayout->setAlignment(Qt::AlignTop);

  QHBoxLayout *headerLayout = new QHBoxLayout();
  appIconLabel = new QLabel();
  appIconLabel->setFixedSize(160, 160);
  appIconLabel->setStyleSheet(
      "background-color: rgba(40,40,50,0.8); border-radius: 16px; border: 1px "
      "solid rgba(255,255,255,0.05);");
  appIconLabel->setAlignment(Qt::AlignCenter);

  QVBoxLayout *titleLayout = new QVBoxLayout();
  appNameLabel = new QLabel("<h1>Welcome to Tiwut Launcher</h1>");
  appNameLabel->setWordWrap(true);
  QLabel *subtitleLabel =
      new QLabel("<span style='color: #aaaaaa; font-size: 14px;'>Select an "
                 "application from the library to view details.</span>");

  titleLayout->addWidget(appNameLabel);
  titleLayout->addWidget(subtitleLabel);
  titleLayout->addStretch();

  headerLayout->addWidget(appIconLabel);
  headerLayout->addSpacing(20);
  headerLayout->addLayout(titleLayout);
  headerLayout->addStretch();

  appDescLabel = new QLabel("");
  appDescLabel->setWordWrap(true);
  appDescLabel->setAlignment(Qt::AlignTop);
  appDescLabel->setMinimumHeight(150);
  appDescLabel->setStyleSheet(
      "font-size: 15px; color: #dddddd; line-height: 1.5;");

  QHBoxLayout *actionLayout = new QHBoxLayout();
  installBtn = new QPushButton("Install");
  launchBtn = new QPushButton("Start");
  launchBtn->setObjectName("LaunchBtn");
  uninstallBtn = new QPushButton("Uninstall");
  uninstallBtn->setObjectName("UninstallBtn");

  installBtn->hide();
  launchBtn->hide();
  uninstallBtn->hide();

  connect(installBtn, &QPushButton::clicked, this,
          &LauncherWindow::installSelectedApp);
  connect(launchBtn, &QPushButton::clicked, this,
          &LauncherWindow::launchSelectedApp);
  connect(uninstallBtn, &QPushButton::clicked, this,
          &LauncherWindow::uninstallSelectedApp);

  actionLayout->addWidget(installBtn);
  actionLayout->addWidget(launchBtn);
  actionLayout->addWidget(uninstallBtn);
  actionLayout->addStretch();

  progressBar = new QProgressBar();
  progressBar->hide();

  rightLayout->addLayout(headerLayout);
  rightLayout->addSpacing(30);
  rightLayout->addWidget(appDescLabel);
  rightLayout->addLayout(actionLayout);
  rightLayout->addSpacing(15);
  rightLayout->addWidget(progressBar);
  rightLayout->addStretch();

  mainLayout->addLayout(leftLayout, 1);
  mainLayout->addLayout(rightLayout, 2);
}

QString LauncherWindow::getAppsDirectory() const {
  QString path =
      QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) +
      "/NexusApps";
  QDir dir(path);
  if (!dir.exists()) {
    dir.mkpath(".");
  }
  return path;
}

QString LauncherWindow::getInterpreterPath() const {
  QString execName = "nexus";
#ifdef Q_OS_WIN
  execName += ".exe";
#endif

  QString path1 = QCoreApplication::applicationDirPath() + "/" + execName;
  if (QFile::exists(path1))
    return path1;

  QString path2 = QCoreApplication::applicationDirPath() + "/../" + execName;
  if (QFile::exists(path2))
    return QDir(path2).absolutePath();

  return path1;
}

void LauncherWindow::checkInstalledApps() {
  QDir appsDir(getAppsDirectory());
  for (auto it = apps.begin(); it != apps.end(); ++it) {
    if (appsDir.exists(it.key())) {
      it->isInstalled = true;
    } else {
      it->isInstalled = false;
    }
  }
}

void LauncherWindow::fetchLibrary() {
  QNetworkRequest request((QUrl(libraryUrl)));
  QNetworkReply *reply = networkManager->get(request);
  connect(reply, &QNetworkReply::finished, this,
          [this, reply]() { onLibraryFetched(reply); });
}

void LauncherWindow::onLibraryFetched(QNetworkReply *reply) {
  if (reply->error() == QNetworkReply::NoError) {
    QByteArray data = reply->readAll();
    QJsonParseError parseError;
    QJsonDocument jsonDoc = QJsonDocument::fromJson(data, &parseError);

    if (parseError.error == QJsonParseError::NoError && jsonDoc.isArray()) {
      apps.clear();
      appListWidget->clear();

      QJsonArray jsonArray = jsonDoc.array();
      for (int i = 0; i < jsonArray.size(); ++i) {
        QJsonObject obj = jsonArray[i].toObject();
        NexusApp app;
        app.id = obj["id"].toString();
        if (app.id.isEmpty())
          app.id = "app_" + QString::number(i);

        app.name = obj["name"].toString();
        app.description = obj["description"].toString();
        app.iconUrl = obj["icon"].toString();
        app.downloadUrl = obj["download_url"].toString();
        app.version = obj["version"].toString();

        apps.insert(app.id, app);

        QListWidgetItem *item = new QListWidgetItem(app.name, appListWidget);
        item->setData(Qt::UserRole, app.id);
      }
      checkInstalledApps();
    } else {
      QMessageBox::warning(this, "JSON Error",
                           "Failed to parse library data as JSON.\nEnsure " +
                               libraryUrl + " provides a valid JSON Array.");
    }
  } else {
    QMessageBox::warning(this, "Network Error",
                         "Failed to fetch library: " + reply->errorString());
  }
  reply->deleteLater();
}

void LauncherWindow::onAppSelected(QListWidgetItem *item) {
  selectedAppId = item->data(Qt::UserRole).toString();
  updateAppDetailsView();
}

void LauncherWindow::updateAppDetailsView() {
  if (!apps.contains(selectedAppId))
    return;

  NexusApp app = apps[selectedAppId];
  appNameLabel->setText("<h1>" + app.name + "</h1>");
  appDescLabel->setText("<b>Version:</b> " + app.version + "<br><br>" +
                        app.description);

  appIconLabel->setText("<b>IMG</b><br>" + app.name.left(3).toUpper());

  if (!app.iconUrl.isEmpty()) {
    QNetworkRequest request((QUrl(app.iconUrl)));
    QNetworkReply *reply = networkManager->get(request);
    connect(reply, &QNetworkReply::finished, [this, reply, id = app.id]() {
      if (reply->error() == QNetworkReply::NoError && selectedAppId == id) {
        QPixmap pixmap;
        if (pixmap.loadFromData(reply->readAll())) {
          appIconLabel->setPixmap(pixmap.scaled(160, 160,
                                                Qt::KeepAspectRatioByExpanding,
                                                Qt::SmoothTransformation));
          appIconLabel->setText("");
        }
      }
      reply->deleteLater();
    });
  }

  if (app.isInstalled) {
    installBtn->hide();
    launchBtn->show();
    uninstallBtn->show();
  } else {
    installBtn->show();
    launchBtn->hide();
    uninstallBtn->hide();
  }
}

void LauncherWindow::installSelectedApp() {
  if (!apps.contains(selectedAppId))
    return;
  NexusApp app = apps[selectedAppId];

  installBtn->setEnabled(false);
  progressBar->setValue(0);
  progressBar->show();

  QNetworkRequest request((QUrl(app.downloadUrl)));
  currentDownload = networkManager->get(request);

  connect(currentDownload, &QNetworkReply::downloadProgress, this,
          &LauncherWindow::onDownloadProgress);
  connect(currentDownload, &QNetworkReply::finished, this,
          &LauncherWindow::onDownloadFinished);
}

void LauncherWindow::onDownloadProgress(qint64 bytesReceived,
                                        qint64 bytesTotal) {
  if (bytesTotal > 0) {
    progressBar->setValue((bytesReceived * 100) / bytesTotal);
  }
}

void LauncherWindow::onDownloadFinished() {
  progressBar->hide();
  installBtn->setEnabled(true);

  if (currentDownload->error() == QNetworkReply::NoError) {
    QString appDirPath = getAppsDirectory() + "/" + selectedAppId;
    QDir().mkpath(appDirPath);

    QFile file(appDirPath + "/main.nx");
    if (file.open(QIODevice::WriteOnly)) {
      file.write(currentDownload->readAll());
      file.close();

      apps[selectedAppId].isInstalled = true;
      updateAppDetailsView();
    } else {
      QMessageBox::warning(this, "File Error",
                           "Failed to save the app file to disk.");
    }
  } else {
    QMessageBox::warning(this, "Download Error",
                         "Failed to download app: " +
                             currentDownload->errorString());
  }

  currentDownload->deleteLater();
  currentDownload = nullptr;
}

void LauncherWindow::uninstallSelectedApp() {
  if (!apps.contains(selectedAppId))
    return;

  int ret = QMessageBox::question(
      this, "Uninstall", "Are you sure you want to uninstall this application?",
      QMessageBox::Yes | QMessageBox::No);
  if (ret == QMessageBox::Yes) {
    QString appDirPath = getAppsDirectory() + "/" + selectedAppId;
    QDir dir(appDirPath);
    if (dir.exists()) {
      dir.removeRecursively();
    }
    apps[selectedAppId].isInstalled = false;
    updateAppDetailsView();
  }
}

void LauncherWindow::launchSelectedApp() {
  if (!apps.contains(selectedAppId))
    return;

  QString appFilePath = getAppsDirectory() + "/" + selectedAppId + "/main.nx";
  QString interpreter = getInterpreterPath();

  if (!QFile::exists(interpreter)) {
    QMessageBox::warning(this, "Interpreter Missing",
                         "Nexus interpreter executable not found at:\n" +
                             interpreter +
                             "\n\nPlease compile interpreter.cpp first.");
    return;
  }

  QProcess *process = new QProcess(this);
  bool success =
      process->startDetached(interpreter, QStringList() << appFilePath);

  if (!success) {
    QMessageBox::warning(this, "Execution Error",
                         "Failed to start the Nexus application.");
  }
}

void LauncherWindow::openSettings() {
  QDialog *dialog = new QDialog(this);
  dialog->setWindowTitle("Settings");
  dialog->resize(500, 400);

  QVBoxLayout *layout = new QVBoxLayout(dialog);
  QTabWidget *tabWidget = new QTabWidget(dialog);
  layout->addWidget(tabWidget);

  QWidget *aboutTab = new QWidget();
  QVBoxLayout *aboutLayout = new QVBoxLayout(aboutTab);
  aboutLayout->addWidget(
      new QLabel("<h2>Tiwut Launcher</h2><p>The Tiwut-Launcher is the official "
                 "desktop </p>"
                 "<p>client designed to provide easy access to all "
                 "applications developed as </p>"
                 "<p>part of the Tiwut hobby project. It functions as an "
                 "application store </p>"
                 "<p>and launcher, allowing users to discover, install, and "
                 "manage Tiwut's </p>"
                 "<p>desktop applications.</p>"
                 "<p>----------------------------------------------------------"
                 "-----------------------------------------------</p>"
                 "</p><p>Powered by: Nexus</p>"
                 "</p><p>License: MIT</p>"
                 "</p><p>Version: v4.1.2</p>"
                 "</p><p>Developer: Tiwut Project</p>"
                 "</p><p>Website: tiwut.org</p>"));
  aboutLayout->addStretch();
  tabWidget->addTab(aboutTab, "About");

  QWidget *themeTab = new QWidget();
  QVBoxLayout *themeLayout = new QVBoxLayout(themeTab);
  themeLayout->addWidget(new QLabel("Theme settings (Coming Soon)"));
  themeLayout->addStretch();
  tabWidget->addTab(themeTab, "Theme");

  QWidget *storageTab = new QWidget();
  QVBoxLayout *storageLayout = new QVBoxLayout(storageTab);
  storageLayout->addWidget(new QLabel("Apps are stored in:"));
  QLineEdit *storageLine = new QLineEdit(getAppsDirectory());
  storageLine->setReadOnly(true);
  storageLayout->addWidget(storageLine);
  storageLayout->addStretch();
  tabWidget->addTab(storageTab, "Storage");

  QWidget *updateTab = new QWidget();
  QVBoxLayout *updateLayout = new QVBoxLayout(updateTab);
  updateLayout->addWidget(new QLabel("Update Nexus Interpreter:"));
  QLineEdit *urlInput = new QLineEdit();
  urlInput->setPlaceholderText("Enter URL to nexus executable");
  QPushButton *downloadBtn = new QPushButton("Download & Replace");
  QProgressBar *updateProgress = new QProgressBar();
  updateProgress->hide();

  updateLayout->addWidget(urlInput);
  updateLayout->addWidget(downloadBtn);
  updateLayout->addWidget(updateProgress);
  updateLayout->addStretch();
  tabWidget->addTab(updateTab, "Update");

  connect(downloadBtn, &QPushButton::clicked, [=]() {
    QString urlStr = urlInput->text();
    if (urlStr.isEmpty())
      return;

    QNetworkRequest request((QUrl(urlStr)));
    QNetworkReply *reply = networkManager->get(request);

    QPointer<QProgressBar> prog = updateProgress;
    QPointer<QPushButton> btn = downloadBtn;
    QPointer<QDialog> dlg = dialog;

    if (prog) {
      prog->setValue(0);
      prog->show();
    }
    if (btn)
      btn->setEnabled(false);

    connect(reply, &QNetworkReply::downloadProgress,
            [prog](qint64 bytesReceived, qint64 bytesTotal) {
              if (prog && bytesTotal > 0) {
                prog->setValue((bytesReceived * 100) / bytesTotal);
              }
            });

    connect(reply, &QNetworkReply::finished, [this, reply, prog, btn, dlg]() {
      if (prog)
        prog->hide();
      if (btn)
        btn->setEnabled(true);

      if (reply->error() == QNetworkReply::NoError) {
        QString execName = "nexus";
#ifdef Q_OS_WIN
        execName += ".exe";
#endif
        QString interpreterPath =
            QCoreApplication::applicationDirPath() + "/" + execName;
        QFile file(interpreterPath);
        if (file.exists())
          file.remove();

        if (file.open(QIODevice::WriteOnly)) {
          file.write(reply->readAll());
          file.setPermissions(QFileDevice::ReadOwner | QFileDevice::WriteOwner |
                              QFileDevice::ExeOwner | QFileDevice::ReadGroup |
                              QFileDevice::ExeGroup | QFileDevice::ReadOther |
                              QFileDevice::ExeOther);
          file.close();
          if (dlg)
            QMessageBox::information(dlg, "Success",
                                     "Interpreter updated successfully!");
        } else {
          if (dlg)
            QMessageBox::warning(dlg, "Error", "Failed to save interpreter.");
        }
      } else {
        if (reply->error() != QNetworkReply::OperationCanceledError) {
          if (dlg)
            QMessageBox::warning(dlg, "Error",
                                 "Download failed: " + reply->errorString());
        }
      }
      reply->deleteLater();
    });
    connect(dlg, &QObject::destroyed, reply, &QNetworkReply::abort);
  });

  dialog->setAttribute(Qt::WA_DeleteOnClose);
  dialog->show();
}

void LauncherWindow::onSearchTextChanged(const QString &text) {
  for (int i = 0; i < appListWidget->count(); ++i) {
    QListWidgetItem *item = appListWidget->item(i);
    bool match = item->text().contains(text, Qt::CaseInsensitive);
    item->setHidden(!match);
  }
}
