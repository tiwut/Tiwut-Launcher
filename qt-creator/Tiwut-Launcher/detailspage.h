#ifndef DETAILSPAGE_H
#define DETAILSPAGE_H

#include <QWidget>
#include "appdata.h"

class AppManager;
class QLabel;
class QPushButton;
class QProgressBar;

class DetailsPage : public QWidget
{
    Q_OBJECT

public:
    explicit DetailsPage(AppManager *appManager, QWidget *parent = nullptr);
    void showApp(const AppData &app, const QString &sourcePage);

signals:
    void backClicked(const QString &sourcePage);

private slots:
    void updateActionButtons();
    void onInstallProgress(int percentage, const QString &status, const QString &info);
    void onInstallFinished(bool success, const QString &message);

private:
    void setupUi();

    AppManager *m_appManager;
    AppData m_currentApp;
    QString m_sourcePage;

    QLabel *m_titleLabel;
    QPushButton *m_installBtn;
    QPushButton *m_uninstallBtn;
    QPushButton *m_launchBtn;
    QPushButton *m_shortcutBtn;
    QPushButton *m_websiteBtn;
    QWidget* m_progressContainer;
    QProgressBar* m_progressBar;
    QLabel* m_statusLabel;
    QLabel* m_infoLabel;
};

#endif
