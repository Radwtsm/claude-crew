# Sul PC di prova, nella sessione di chi è allo schermo: apre la Sandbox (se c'è un .wsb) e tiene sveglio il PC con
# lo schermo acceso finché resta aperta, poi lascia di nuovo fare allo standby. Le impostazioni di Windows non cambiano.
param([string]$Wsb)
Add-Type -Namespace Pleyades -Name Energia -MemberDefinition @'
[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint s);
[DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, uint f, System.UIntPtr e);
'@
# 0x80000003 = CONTINUOUS | SYSTEM | DISPLAY in decimale: in PowerShell 5.1 «0x80000003» è un Int32 negativo, la
# chiamata falliva senza dirlo (finestra nascosta) e dopo 15 min il PC andava in standby a metà prova
if (-not [Pleyades.Energia]::SetThreadExecutionState([uint32]2147483651)) {
    "$(Get-Date -Format HH:mm:ss) sveglia: SetThreadExecutionState non va" | Add-Content "$PSScriptRoot\sveglia.txt" }
[Pleyades.Energia]::keybd_event(0x10, 0, 0, [UIntPtr]::Zero); [Pleyades.Energia]::keybd_event(0x10, 0, 2, [UIntPtr]::Zero)  # Shift: schermo acceso
if ($Wsb) { Start-Process WindowsSandbox.exe "`"$Wsb`""; Start-Sleep 60 }
while (Get-Process WindowsSandboxServer, WindowsSandboxRemoteSession -ErrorAction SilentlyContinue) { Start-Sleep 30 }
[Pleyades.Energia]::SetThreadExecutionState([uint32]2147483648) | Out-Null
