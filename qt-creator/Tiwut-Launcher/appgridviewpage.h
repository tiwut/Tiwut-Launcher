#ifndef APPGRIDVIEWPAGE_H
#define APPGRIDVIEWPAGE_H

#include <QWidget>
#include "appdata.h"

class AppManager;
class QLineEdit;
class QGridLayout;
class QScrollArea;
class AppCard;

class AppGridViewPage : public QWidget
{
    Q_OBJECT
public:
    explicit AppGridViewPage(const QString &title, AppManager *appManager, QWidget *parent = nullptr);
    void populate(const QList<AppData> &apps);

signals:
    void appSelected(const AppData &app, const QString &sourcePage);

private slots:
    void filterApps(const QString &text);
    void onAppCardClicked(const AppData &app);
    void onIconReady(const QUrl &url, const QPixmap &pixmap);

private:
    void clearGrid();
    void repopulateGrid();

    QString m_pageName;
    AppManager *m_appManager;
    QLineEdit *m_searchBar;
    QGridLayout *m_gridLayout;
    QScrollArea *m_scrollArea;
    QList<AppData> m_allAppsOnPage;
    QList<AppData> m_appsToDisplay;
    QList<AppCard*> m_appCards;
};
#endif
