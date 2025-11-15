#include "appcard.h"
#include "appconfig.h"
#include <QVBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QMouseEvent>

AppCard::AppCard(const AppData &app, QWidget *parent)
    : QFrame(parent), m_app(app)
{
    setFrameShape(QFrame::StyledPanel);
    setFrameShadow(QFrame::Raised);
    setCursor(Qt::PointingHandCursor);
    setFixedSize(220, 180);
    setStyleSheet(QString("AppCard { background-color: %1; border: 1px solid %1; border-radius: 5px; }")
                      .arg(AppConfig::Primary.name()));

    QVBoxLayout *layout = new QVBoxLayout(this);
    layout->setContentsMargins(10, 10, 10, 10);
    layout->setSpacing(10);

    m_iconLabel = new QLabel(this);
    m_iconLabel->setFixedSize(180, 100);
    m_iconLabel->setAlignment(Qt::AlignCenter);
    m_iconLabel->setStyleSheet(QString("background-color: %1; border-radius: 3px;").arg(AppConfig::Secondary.name()));
    m_iconLabel->setText("Loading...");

    m_nameLabel = new QLabel(m_app.name, this);
    m_nameLabel->setFont(AppConfig::FontBodyBold);
    m_nameLabel->setAlignment(Qt::AlignCenter);
    m_nameLabel->setWordWrap(true);

    layout->addWidget(m_iconLabel, 0, Qt::AlignHCenter);
    layout->addWidget(m_nameLabel);
    layout->addStretch();
}

const AppData& AppCard::getAppData() const {
    return m_app;
}

void AppCard::setIcon(const QPixmap &pixmap) {
    if (!pixmap.isNull()) {
        m_iconLabel->setPixmap(pixmap.scaled(m_iconLabel->size(), Qt::KeepAspectRatio, Qt::SmoothTransformation));
    } else {
        m_iconLabel->setText("No Icon");
    }
}

void AppCard::mousePressEvent(QMouseEvent *event) {
    if (event->button() == Qt::LeftButton) {
        emit clicked(m_app);
    }
    QFrame::mousePressEvent(event);
}

void AppCard::enterEvent(QEnterEvent *event) {
    setStyleSheet(QString("AppCard { background-color: %1; border: 1px solid %2; border-radius: 5px; }")
                      .arg(AppConfig::Secondary.name()).arg(AppConfig::Accent.name()));
    QFrame::enterEvent(event);
}

void AppCard::leaveEvent(QEvent *event) {
    setStyleSheet(QString("AppCard { background-color: %1; border: 1px solid %1; border-radius: 5px; }")
                      .arg(AppConfig::Primary.name()));
    QFrame::leaveEvent(event);
}
