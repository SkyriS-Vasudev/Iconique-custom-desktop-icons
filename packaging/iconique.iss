#ifndef MyAppName
  #define MyAppName "Iconique"
#endif
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#ifndef MyAppPublisher
  #define MyAppPublisher "Iconique"
#endif
#ifndef MyAppPublisherURL
  #define MyAppPublisherURL "https://github.com/SkyriS-Vasudev/Iconique-custom-desktop-icons"
#endif
#ifndef MyAppSupportURL
  #define MyAppSupportURL "https://github.com/SkyriS-Vasudev/Iconique-custom-desktop-icons/issues"
#endif
#ifndef MyAppUpdatesURL
  #define MyAppUpdatesURL "https://github.com/SkyriS-Vasudev/Iconique-custom-desktop-icons/releases"
#endif
#define MyAppExeName "Iconique.exe"

[Setup]
SourceDir=..
AppId={{0D7F1E5C-3F17-4B16-8DBD-5F0D0459C13C}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppPublisherURL}
AppSupportURL={#MyAppSupportURL}
AppUpdatesURL={#MyAppUpdatesURL}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installer
VersionInfoProductName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
DefaultDirName={autopf}\Iconique
DefaultGroupName=Iconique
OutputDir=packaging\installer-output
OutputBaseFilename=IconiqueSetup-{#MyAppVersion}
SetupIconFile=packaging\iconique.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=no
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

[Tasks]
Name: desktopicon; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\Iconique\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Iconique"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Iconique"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Iconique"; Flags: nowait postinstall skipifsilent
