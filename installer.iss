; Inno Setup Script for Formato Image Converter
; This script creates a professional Windows installer with an icon and desktop shortcut

[Setup]
; Basic app information
AppName=Formato Image Converter
AppVersion=0.1
AppPublisher=MRThugh
AppPublisherURL=https://github.com/MRThugh/Formato-Image-Converter
DefaultDirName={pf}\Formato
DefaultGroupName=Formato
AllowNoIcons=yes
OutputBaseFilename=FormatoSetup
Compression=lzma
SolidCompression=yes
SetupIconFile=assets\icon.ico

; Optional: Enable administrative install mode
PrivilegesRequired=admin

[Files]
; Main executable and required files
Source: "dist\Formato.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
; Add other required files here (images, DLLs, etc.)

[Icons]
; Start menu shortcut
Name: "{group}\Formato Image Converter"; Filename: "{app}\Formato.exe"; IconFilename: "{app}\assets\icon.ico"
; Desktop shortcut
Name: "{commondesktop}\Formato Image Converter"; Filename: "{app}\Formato.exe"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Tasks]
; Optional desktop shortcut
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
; Run the app after installation
Filename: "{app}\Formato.exe"; Description: "Launch Formato Image Converter"; Flags: nowait postinstall skipifsilent
