#include "mainwindow.h"
#include "appconfig.h"
#include "discoverpage.h" // Sie müssen diese Klasse noch erstellen
#include "librarypage.h"  // Sie müssen diese Klasse noch erstellen

#include <QHBoxLayout>
#include <QListWidgetItem>

MainWindow::MainWindow(QWidget *parent) : QMainWindow(parent) {
    setupUi();
    setupConnections();

    // Initial-Styling
    setStyleSheet(QString("background-color: %1;").arg(AppConfig::BACKGROUND_COLOR.name()));
}

MainWindow::~MainWindow() {}

void MainWindow::setupUi() {
    centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);

    QHBoxLayout *mainLayout = new QHBoxLayout(centralWidget);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    // Navigationsleiste
    navigationList = new QListWidget(this);
    navigationList->setFixedWidth(200);
    navigationList->addItem("Discover");
    navigationList->addItem("My Library");

    // Seiten-Container
    stackedWidget = new QStackedWidget(this);
    discoverPage = new DiscoverPage(this); // Annahme, dass diese Klasse existiert
    libraryPage = new LibraryPage(this);   // Annahme, dass diese Klasse existiert

    stackedWidget->addWidget(discoverPage);
    stackedWidget->addWidget(libraryPage);

    mainLayout->addWidget(navigationList);
    mainLayout->addWidget(stackedWidget);

    setWindowTitle("Tiwut App Store");
    resize(1100, 750);
}

void MainWindow::setupConnections() {
    connect(navigationList, &QListWidget::itemClicked, this, &MainWindow::onNavigationItemSelected);
}

void MainWindow::onNavigationItemSelected(QListWidgetItem *item) {
    if (item->text() == "Discover") {
        stackedWidget->setCurrentWidget(discoverPage);
    } else if (item->text() == "My Library") {
        stackedWidget->setCurrentWidget(libraryPage);
    }
}
