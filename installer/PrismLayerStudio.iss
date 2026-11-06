#define AppName "Prism Layer Studio"
#define AppVersion "2.6.0"
#define AppExe "PrismLayerStudio.exe"

[Setup]
AppId={{E79C7545-C719-45BD-BC2F-B371EEACD0F6}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Prism Layer Studio
AppCopyright=Prism Layer Studio
DefaultDirName={localappdata}\Programs\PrismLayerStudio
DefaultGroupName={#AppName}
DisableDirPage=no
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
MinVersion=10.0.17763
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release
OutputBaseFilename=PrismLayerStudio-Setup
SetupIconFile=..\assets\prism-layer-studio.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName} {#AppVersion}
VersionInfoVersion={#AppVersion}.0
VersionInfoDescription=Prism Layer Studio Offline Installer
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\release\PrismLayerStudio.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\prism-layer-studio.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\vendor\MicrosoftEdgeWebView2RuntimeInstallerX64.exe"; Flags: dontcopy
Source: "..\build\installer-licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion
Source: "..\USER_GUIDE.zh-CN.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{group}\Uninstall Prism Layer Studio"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[Code]
const
  WebViewKey = 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}';

function InitializeSetup(): Boolean;
var
  Release: Cardinal;
begin
  Result := (RegQueryDWordValue(HKLM32, 'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full', 'Release', Release) and (Release >= 394802)) or
    (RegQueryDWordValue(HKLM64, 'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full', 'Release', Release) and (Release >= 394802));
  if not Result then MsgBox('Microsoft .NET Framework 4.6.2 or later is required by the Windows desktop container. Windows 10 1809 and Windows 11 include a newer version. Repair or enable .NET Framework, then run Setup again.', mbError, MB_OK);
end;

function SupportedVersion(Version: String): Boolean;
var
  Dot: Integer;
begin
  Dot := Pos('.', Version);
  if Dot > 0 then Version := Copy(Version, 1, Dot - 1);
  Result := StrToIntDef(Version, 0) >= 109;
end;

function UsableRuntime(FileName: String): Boolean;
var
  Version: String;
begin
  Result := FileExists(FileName) and GetVersionNumbersString(FileName, Version);
  if Result then Result := SupportedVersion(Version);
end;

function RuntimeIn(Base: String): Boolean;
var
  FindRec: TFindRec;
begin
  Result := False;
  if FindFirst(Base + '\*', FindRec) then begin
    try
      repeat
        if (FindRec.Name <> '.') and (FindRec.Name <> '..') and
           ((FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY) <> 0) then
          if UsableRuntime(Base + '\' + FindRec.Name + '\msedgewebview2.exe') then begin
            Result := True;
            Break;
          end;
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
end;

function RegisteredRuntime(Root: Integer; Base: String): Boolean;
var
  Version: String;
begin
  Result := RegQueryStringValue(Root, WebViewKey, 'pv', Version);
  if Result then Result := SupportedVersion(Version) and
    UsableRuntime(Base + '\' + Version + '\msedgewebview2.exe');
end;

function HasWebView2(): Boolean;
var
  MachineBase, NativeBase, UserBase: String;
begin
  MachineBase := ExpandConstant('{pf32}\Microsoft\EdgeWebView\Application');
  NativeBase := ExpandConstant('{pf64}\Microsoft\EdgeWebView\Application');
  UserBase := ExpandConstant('{localappdata}\Microsoft\EdgeWebView\Application');
  Result := RegisteredRuntime(HKLM32, MachineBase) or
    RegisteredRuntime(HKLM64, NativeBase) or
    RegisteredRuntime(HKCU32, UserBase) or
    RegisteredRuntime(HKCU64, UserBase) or
    RuntimeIn(MachineBase) or RuntimeIn(NativeBase) or RuntimeIn(UserBase);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Code, Attempts: Integer;
  Installer: String;
begin
  Result := '';
  if HasWebView2() then begin
    Log('Usable WebView2 runtime >= 109 already present.');
    Exit;
  end;
  WizardForm.StatusLabel.Caption := 'Installing Microsoft Edge WebView2 Runtime (offline)...';
  ExtractTemporaryFile('MicrosoftEdgeWebView2RuntimeInstallerX64.exe');
  Installer := ExpandConstant('{tmp}\MicrosoftEdgeWebView2RuntimeInstallerX64.exe');
  if not Exec(Installer, '/silent /install', '', SW_HIDE, ewWaitUntilTerminated, Code) then begin
    Result := 'Cannot run the bundled Microsoft WebView2 offline installer. Windows error: ' + IntToStr(Code);
    Exit;
  end;
  Log('Microsoft WebView2 installer exit code: ' + IntToStr(Code));
  if (Code <> 0) and (Code <> 3010) and (Code <> 1641) then begin
    { Another installer can report already installed; accept only if runtime is actually usable. }
    if not HasWebView2() then begin
      Result := 'Microsoft WebView2 installation failed (code ' + IntToStr(Code) + '). Contact your administrator, then run Setup again.';
      Exit;
    end;
  end;
  if (Code = 3010) or (Code = 1641) then NeedsRestart := True;
  Attempts := 0;
  while (not HasWebView2()) and (Attempts < 20) do begin
    Sleep(500);
    Attempts := Attempts + 1;
  end;
  if not HasWebView2() then Result := 'Microsoft WebView2 was not detected after installation. Restart Windows and run Setup again.';
end;
