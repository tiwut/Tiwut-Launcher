#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include "appdata.h"

class QStackedWidget;
class QListWidget;
class AppManager;
class DetailsPage;
class AppGridViewPage;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

public slots:
    void showDetailsPage(const AppData &app, const QString &sourcePage);

private slots:
    void onLibraryLoaded();
    void onNavigationChanged(int index);
    void goBackToPage(const QString &sourcePage);
    void updatePages();

private:
    void setupUi();
    void applyStyles();
    void createPages();

    QStackedWidget *m_stackedWidget;
    QListWidget *m_navRail;
    AppManager *m_appManager;

    AppGridViewPage *m_discoverPage;
    AppGridViewPage *m_libraryPage;
    DetailsPage *m_detailsPage;
};

#endif
