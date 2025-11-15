#include "mainwindow.h"
#include "appconfig.h"
#include "appmanager.h"
#include "appgridviewpage.h"
#include "detailspage.h"

#include <QHBoxLayout>
#include <QListWidget>
#include <QStackedWidget>
#include <QLabel>
#include <QApplication>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), m_appManager(new AppManager(this))
{
    setupUi();
    applyStyles();
    createPages();

    connect(m_navRail, &QListWidget::currentRowChanged, this, &MainWindow::onNavigationChanged);
    connect(m_appManager, &AppManager::libraryLoaded, this, &MainWindow::onLibraryLoaded);
    connect(m_appManager, &AppManager::appStatusChanged, this, &MainWindow::updatePages);

    m_appManager->loadLibrary();
}

MainWindow::~MainWindow() {}

void MainWindow::setupUi() {
    setWindowTitle("Tiwut App Store");
    resize(1100, 750);
    setMinimumSize(800, 600);

    QWidget *centralWidget = new QWidget(this);
    QHBoxLayout *mainLayout = new QHBoxLayout(centralWidget);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    m_navRail = new QListWidget(this);
    m_navRail->setFixedWidth(200);
    auto *titleLabel = new QLabel("TIWUT STORE");
    titleLabel->setFont(QFont("Segoe UI", 16, QFont::Bold));
    titleLabel->setAlignment(Qt::AlignCenter);
    titleLabel->setContentsMargins(10, 25, 10, 25);
    QListWidgetItem* titleItem = new QListWidgetItem(m_navRail);
    titleItem->setSizeHint(titleLabel->sizeHint());
    titleItem->setFlags(titleItem->flags() & ~Qt::ItemIsSelectable);
    m_navRail->setItemWidget(titleItem, titleLabel);

    m_navRail->addItem("Discover");
    m_navRail->addItem("My Library");

    m_stackedWidget = new QStackedWidget(this);
    mainLayout->addWidget(m_navRail);
    mainLayout->addWidget(m_stackedWidget, 1);
    setCentralWidget(centralWidget);
}

void MainWindow::createPages() {
    m_discoverPage = new AppGridViewPage("Discover New Apps", m_appManager, this);
    m_libraryPage = new AppGridViewPage("My Installed Apps", m_appManager, this);
    m_detailsPage = new DetailsPage(m_appManager, this);

    m_stackedWidget->addWidget(m_discoverPage);
    m_stackedWidget->addWidget(m_libraryPage);
    m_stackedWidget->addWidget(m_detailsPage);

    connect(m_discoverPage, &AppGridViewPage::appSelected, this, &MainWindow::showDetailsPage);
    connect(m_libraryPage, &AppGridViewPage::appSelected, this, &MainWindow::showDetailsPage);
    connect(m_detailsPage, &DetailsPage::backClicked, this, &MainWindow::goBackToPage);
}

void MainWindow::applyStyles() {
    QString style = QString(
                        ).arg(AppConfig::Background.name())
                        .arg(AppConfig::Secondary.name());
    qApp->setStyleSheet(style);

    if (auto titleLabel = m_navRail->findChild<QLabel*>()) {
        titleLabel->setObjectName("TitleLabel");
    }

    for(int i = 1; i < m_navRail->count(); ++i) {
        m_navRail->item(i)->setFont(AppConfig::FontNav);
    }
}

void MainWindow::onLibraryLoaded() {
    updatePages();
    m_navRail->setCurrentRow(1);
}

void MainWindow::updatePages() {
    m_discoverPage->populate(m_appManager->getAllApps());
    m_libraryPage->populate(m_appManager->getInstalledApps());
}

void MainWindow::onNavigationChanged(int index) {
    if (index == 1) {
        m_stackedWidget->setCurrentWidget(m_discoverPage);
    } else if (index == 2) {
        m_stackedWidget->setCurrentWidget(m_libraryPage);
    }
}

void MainWindow::showDetailsPage(const AppData &app, const QString &sourcePage) {
    m_detailsPage->showApp(app, sourcePage);
    m_stackedWidget->setCurrentWidget(m_detailsPage);
}

void MainWindow::goBackToPage(const QString &sourcePage) {
    if (sourcePage == "DiscoverPage") {
        m_navRail->setCurrentRow(1);
    } else if (sourcePage == "LibraryPage") {
        m_navRail->setCurrentRow(2);
    }
}
