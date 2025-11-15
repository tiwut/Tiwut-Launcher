
#include "appconfig.h"


const QString AppConfig::APP_DATA_DIR = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) + "/TiwutLauncher";
const QString AppConfig::ICON_CACHE_DIR = AppConfig::APP_DATA_DIR + "/icon_cache";
const QString AppConfig::INSTALL_SUBDIR = "TiwutApps";
const QString AppConfig::INSTALL_BASE_PATH = QStandardPaths::writableLocation(QStandardPaths::DocumentsLocation) + "/" + AppConfig::INSTALL_SUBDIR;

const QString AppConfig::LIBRARY_URL = "https://launcher.tiwut.de/library.tiwut";

const QColor AppConfig::Background    = QColor(46, 46, 46);
const QColor AppConfig::Primary       = QColor(60, 60, 60);
const QColor AppConfig::Secondary     = QColor(80, 80, 80);
const QColor AppConfig::Accent        = QColor(0, 120, 215);
const QColor AppConfig::AccentHover   = QColor(0, 152, 255);
const QColor AppConfig::Text          = QColor(255, 255, 255);
const QColor AppConfig::TextSecondary = QColor(176, 176, 176);

const QFont AppConfig::FontLargeTitle = QFont("Segoe UI", 24, QFont::Bold);
const QFont AppConfig::FontTitle      = QFont("Segoe UI", 14, QFont::Bold);
const QFont AppConfig::FontBody       = QFont("Segoe UI", 10);
const QFont AppConfig::FontBodyBold   = QFont("Segoe UI", 10, QFont::Bold);
const QFont AppConfig::FontNav        = QFont("Segoe UI", 11, QFont::Bold);
