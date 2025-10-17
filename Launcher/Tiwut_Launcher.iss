; Inno Setup Script - Modernized & Compatible Version
; For a real application, you should generate a new GUID for AppId.

[Setup]
; --- GRUNDLEGENDE INFORMATIONEN ---
; WICHTIG: Generiere eine NEUE AppId für dein Projekt! (In Inno Setup: Tools -> Generate GUID)
AppId={{DEINE-NEUE-GUID-HIER}
AppName=Tiwut Launcher
AppVersion=2.2
AppPublisher=Tiwut
AppPublisherURL=https://tiwut.de
AppSupportURL=https://tiwut.de
AppUpdatesURL=https://tiwut.de
DefaultDirName={localappdata}\Tiwut Launcher
DefaultGroupName=Tiwut Launcher
DisableProgramGroupPage=yes
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
OutputDir=C:\Users\Tiwut\Desktop
OutputBaseFilename=Tiwut-Launcher-Setup
SetupIconFile=F:/GitHub/Respo/Tiwut.de/icon.ico
LicenseFile=C:/Users/Tiwut/Desktop/LICENSE.txt
WizardStyle=modern

; --- Visuelles Design & Branding ---
; Eigenes Bild für die linke Seite des Wizards.
WizardImageFile=setup-wizard-image.bmp
; Eigenes kleines Logo für die obere rechte Ecke.
WizardSmallImageFile=setup-header-image.bmp
WizardImageStretch=no

; ENTFERNT: Die folgenden WizardColor-Befehle wurden entfernt, da sie
; nur von Inno Setup 6 und neuer unterstützt werden.
; WizardColorGeneral=$2D2D30
; WizardColorInner=$3F3F46
; WizardColorText=$FFFFFF
; WizardColorTitle=$FFFFFF
; WizardColorHeader=$00ACC1

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
Source: "F:/GitHub/Respo/Tiwut-Launcher/Updater/release_1.2/LauncherCheck.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "F:/GitHub/Respo/Tiwut-Launcher/Updater/release_1.2/*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Tiwut Launcher"; Filename: "{app}\LauncherCheck.exe"
Name: "{autodesktop}\Tiwut Launcher"; Filename: "{app}\LauncherCheck.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\LauncherCheck.exe"; Description: "{cm:LaunchProgram,Tiwut Launcher}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

