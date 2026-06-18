#define MyAppName "Iconique"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Iconique"
#define MyAppExeName "Iconique.exe"

[Setup]
AppId={{0D7F1E5C-3F17-4B16-8DBD-5F0D0459C13C}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Iconique
DefaultGroupName=Iconique
OutputDir=installer-output
OutputBaseFilename=IconiqueSetup
SetupIconFile=packaging\iconique.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=no
PrivilegesRequired=admin

[Tasks]
Name: desktopicon; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\Iconique\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Iconique"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Iconique"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Iconique"; Flags: nowait postinstall skipifsilent
