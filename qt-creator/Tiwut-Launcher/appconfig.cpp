#include "appconfig.h"

const QString AppConfig::APP_DATA_DIR = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) + "/TiwutLauncher";
const QString AppConfig::ICON_CACHE_DIR = APP_DATA_DIR + "/icon_cache";
const QString AppConfig::INSTALL_BASE_PATH = QStandardPaths::writableLocation(QStandardPaths::DocumentsLocation) + "/TiwutApps";
const QString AppConfig::LIBRARY_URL = "https://launcher.tiwut.de/library.tiwut";

// Styling
const QString AppConfig::THEME = "clam";
const QColor AppConfig::BACKGROUND_COLOR = QColor("#2E2E2E");
const QColor AppConfig::PRIMARY_COLOR = QColor("#3C3C3C");
// ...
