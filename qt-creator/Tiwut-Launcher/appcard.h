#ifndef APPCARD_H
#define APPCARD_H

#include <QFrame>
#include "appdata.h"

class QLabel;
class QPushButton;

class AppCard : public QFrame
{
    Q_OBJECT
public:
    explicit AppCard(const AppData &app, QWidget *parent = nullptr);

    const AppData& getAppData() const;
    void setIcon(const QPixmap &pixmap);

signals:
    void clicked(const AppData &app);

protected:
    void mousePressEvent(QMouseEvent *event) override;
    void enterEvent(QEnterEvent *event) override;
    void leaveEvent(QEvent *event) override;

private:
    AppData m_app;
    QLabel *m_iconLabel;
    QLabel *m_nameLabel;
};

#endif
