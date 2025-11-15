#include "detailspage.h"
#include "appmanager.h"
#include "appconfig.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QProgressBar>
#include <QMessageBox>
#include <QDesktopServices>
#include <QUrl>

DetailsPage::DetailsPage(AppManager *appManager, QWidget *parent)
    : QWidget(parent), m_appManager(appManager)
{
    setupUi();

    connect(m_appManager, &AppManager::installProgress, this, &DetailsPage::onInstallProgress);
    connect(m_appManager, &AppManager::installFinished, this, &DetailsPage::onInstallFinished);
    connect(m_appManager, &AppManager::appStatusChanged, this, &DetailsPage::updateActionButtons);
}

void DetailsPage::setupUi() {
    QVBoxLayout *mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(25, 20, 25, 25);
    mainLayout->setSpacing(15);

    QHBoxLayout *headerLayout = new QHBoxLayout;
    QPushButton *backButton = new QPushButton("< Back");
    connect(backButton, &QPushButton::clicked, [this](){ emit backClicked(m_sourcePage); });
    headerLayout->addWidget(backButton);
    headerLayout->addStretch();

    QHBoxLayout *titleLayout = new QHBoxLayout;
    m_titleLabel = new QLabel("App Name");
    m_titleLabel->setFont(AppConfig::FontLargeTitle);
    titleLayout->addWidget(m_titleLabel);
    titleLayout->addStretch();

    m_installBtn = new QPushButton("Install");
    m_uninstallBtn = new QPushButton("Uninstall");
    m_launchBtn = new QPushButton("Launch");
    m_shortcutBtn = new QPushButton("Create Shortcut");
    titleLayout->addWidget(m_installBtn);
    titleLayout->addWidget(m_uninstallBtn);
    titleLayout->addWidget(m_launchBtn);
    titleLayout->addWidget(m_shortcutBtn);

    connect(m_installBtn, &QPushButton::clicked, [this](){ m_appManager->installApp(m_currentApp); });
    connect(m_uninstallBtn, &QPushButton::clicked, [this](){ m_appManager->uninstallApp(m_currentApp); });
    connect(m_launchBtn, &QPushButton::clicked, [this](){ m_appManager->launchApp(m_currentApp); });
    connect(m_shortcutBtn, &QPushButton::clicked, [this](){ m_appManager->createShortcut(m_currentApp); });

    QLabel *aboutLabel = new QLabel("About this App");
    aboutLabel->setFont(AppConfig::FontTitle);
    QLabel *infoTextLabel = new QLabel("For detailed information, please visit the official website.");
    m_websiteBtn = new QPushButton("Open Website");
    connect(m_websiteBtn, &QPushButton::clicked, [this](){ QDesktopServices::openUrl(m_currentApp.websiteUrl); });

    mainLayout->addLayout(headerLayout);
    mainLayout->addLayout(titleLayout);
    mainLayout->addSpacing(20);
    mainLayout->addWidget(aboutLabel);
    mainLayout->addWidget(infoTextLabel);
    mainLayout->addWidget(m_websiteBtn, 0, Qt::AlignLeft);
    mainLayout->addStretch();

    m_progressContainer = new QWidget(this);
    QVBoxLayout *progressLayout = new QVBoxLayout(m_progressContainer);
    m_statusLabel = new QLabel("Status...");
    m_progressBar = new QProgressBar();
    m_infoLabel = new QLabel("Info...");
    progressLayout->addWidget(m_statusLabel);
    progressLayout->addWidget(m_progressBar);
    progressLayout->addWidget(m_infoLabel);
    mainLayout->addWidget(m_progressContainer);
    m_progressContainer->setVisible(false);
}

void DetailsPage::showApp(const AppData &app, const QString &sourcePage) {
    m_currentApp = app;
    m_sourcePage = sourcePage;
    m_titleLabel->setText(m_currentApp.name);
    m_progressContainer->setVisible(false);
    m_installBtn->setEnabled(true);
    updateActionButtons();
}

void DetailsPage::updateActionButtons() {
    bool isInstalled = m_appManager->isAppInstalled(m_currentApp);
    m_installBtn->setVisible(!isInstalled);
    m_uninstallBtn->setVisible(isInstalled);
    m_launchBtn->setVisible(isInstalled);
    m_shortcutBtn->setVisible(isInstalled);
}

void DetailsPage::onInstallProgress(int percentage, const QString &status, const QString &info) {
    m_progressContainer->setVisible(true);
    m_installBtn->setEnabled(false);
    m_progressBar->setValue(percentage);
    m_statusLabel->setText(status);
    m_infoLabel->setText(info);
}

void DetailsPage::onInstallFinished(bool success, const QString &message) {
    m_progressContainer->setVisible(false);
    m_installBtn->setEnabled(true);
    updateActionButtons();
    if (success) {
        QMessageBox::information(this, "Success", message);
    } else {
        QMessageBox::critical(this, "Error", message);
    }
}
