#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QStackedWidget>
#include <QListWidget>

class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void onNavigationItemSelected(QListWidgetItem *item);

private:
    void setupUi();
    void setupConnections();

    QWidget *centralWidget;
    QListWidget *navigationList;
    QStackedWidget *stackedWidget;

    // Seiten-Widgets
    QWidget *discoverPage;
    QWidget *libraryPage;
};

#endif // MAINWINDOW_H
