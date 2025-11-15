#include "appgridviewpage.h"
#include "appmanager.h"
#include "appconfig.h"
#include "appcard.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QScrollArea>
#include <QGridLayout>

AppGridViewPage::AppGridViewPage(const QString &title, AppManager *appManager, QWidget *parent)
    : QWidget(parent), m_appManager(appManager)
{
    m_pageName = (title.contains("Discover") ? "DiscoverPage" : "LibraryPage");
    QVBoxLayout *mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(25, 20, 25, 10);

    QHBoxLayout *headerLayout = new QHBoxLayout();
    QLabel *titleLabel = new QLabel(title, this);
    titleLabel->setFont(AppConfig::FontLargeTitle);
    m_searchBar = new QLineEdit(this);
    m_searchBar->setPlaceholderText("Search...");
    m_searchBar->setFixedWidth(250);
    headerLayout->addWidget(titleLabel);
    headerLayout->addStretch();
    headerLayout->addWidget(m_searchBar);

    m_scrollArea = new QScrollArea(this);
    m_scrollArea->setWidgetResizable(true);
    m_scrollArea->setStyleSheet("QScrollArea { border: none; }");
    QWidget *scrollWidget = new QWidget;
    m_gridLayout = new QGridLayout(scrollWidget);
    m_gridLayout->setSpacing(15);
    m_scrollArea->setWidget(scrollWidget);

    mainLayout->addLayout(headerLayout);
    mainLayout->addWidget(m_scrollArea);

    connect(m_searchBar, &QLineEdit::textChanged, this, &AppGridViewPage::filterApps);
    connect(m_appManager, &AppManager::iconReady, this, &AppGridViewPage::onIconReady);
}

void AppGridViewPage::populate(const QList<AppData> &apps) {
    m_allAppsOnPage = apps;
    filterApps(m_searchBar->text());
}

void AppGridViewPage::filterApps(const QString &text) {
    m_appsToDisplay.clear();
    if (text.isEmpty()) {
        m_appsToDisplay = m_allAppsOnPage;
    } else {
        for (const auto &app : m_allAppsOnPage) {
            if (app.name.contains(text, Qt::CaseInsensitive)) {
                m_appsToDisplay.append(app);
            }
        }
    }
    repopulateGrid();
}

void AppGridViewPage::clearGrid() {
    qDeleteAll(m_appCards);
    m_appCards.clear();
}

void AppGridViewPage::repopulateGrid() {
    clearGrid();

    int cols = qMax(1, (m_scrollArea->width() - 50) / 235);
    int row = 0, col = 0;

    for (const auto &app : m_appsToDisplay) {
        AppCard *card = new AppCard(app);
        connect(card, &AppCard::clicked, this, &AppGridViewPage::onAppCardClicked);
        m_gridLayout->addWidget(card, row, col);
        m_appCards.append(card);
        m_appManager->getIcon(app);

        col++;
        if (col >= cols) {
            col = 0;
            row++;
        }
    }
}

void AppGridViewPage::onAppCardClicked(const AppData &app) {
    emit appSelected(app, m_pageName);
}

void AppGridViewPage::onIconReady(const QUrl &url, const QPixmap &pixmap) {
    for (AppCard *card : m_appCards) {
        if (card->getAppData().iconUrl == url) {
            card->setIcon(pixmap);
        }
    }
}
