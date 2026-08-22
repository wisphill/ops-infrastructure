PS = powershell.exe -NoProfile -ExecutionPolicy Bypass -Command
APP_NAME = WindowsCommandServer
SCRIPT_NAME = command-server.ps1
PORT = 41020

.PHONY: install uninstall start stop status

install:
	@echo "Installing $(SCRIPT_NAME) and setting up autostart..."
	@$(PS) "\
		$$dir = $$env:APPDATA + '\$(APP_NAME)'; \
		if (!(Test-Path $$dir)) { New-Item -ItemType Directory -Path $$dir | Out-Null }; \
		$$target = $$dir + '\$(SCRIPT_NAME)'; \
		Copy-Item -Path '.\$(SCRIPT_NAME)' -Destination $$target -Force; \
		$$q = [char]34; $$sq = [char]39; \
		$$args = '-ExecutionPolicy Bypass -WindowStyle Hidden -File ' + $$q + $$target + $$q; \
		$$bootCmd = 'powershell.exe -WindowStyle Hidden -Command Start-Process powershell.exe -Verb RunAs -ArgumentList ' + $$sq + $$args + $$sq; \
		Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name '$(APP_NAME)' -Value $$bootCmd; \
		Write-Host '[OK] Installed successfully to:' $$dir -ForegroundColor Green; \
		Write-Host '[OK] Added to Windows Startup (Will trigger UAC on boot).' -ForegroundColor Green \
	"

uninstall:
	@echo "Uninstalling $(APP_NAME)..."
	@$(PS) "\
		$$dir = $$env:APPDATA + '\$(APP_NAME)'; \
		Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name '$(APP_NAME)' -ErrorAction SilentlyContinue; \
		$$sq = [char]39; \
		$$killCmd = 'Get-CimInstance Win32_Process | Where-Object { $$_.ProcessId -ne $$PID -and $$_.CommandLine -match ' + $$sq + '$(SCRIPT_NAME)' + $$sq + ' } | Invoke-CimMethod -MethodName Terminate'; \
		Start-Process powershell.exe -Verb RunAs -WindowStyle Hidden -ArgumentList @('-Command', $$killCmd); \
		Start-Sleep -Seconds 2; \
		if (Test-Path $$dir) { Remove-Item -Recurse -Force $$dir }; \
		Write-Host '[OK] Uninstalled and cleaned up successfully.' -ForegroundColor Yellow \
	"

start:
	@echo "Starting $(APP_NAME) as Administrator in background..."
	@$(PS) "\
		$$target = $$env:APPDATA + '\$(APP_NAME)\$(SCRIPT_NAME)'; \
		$$q = [char]34; \
		$$args = '-ExecutionPolicy Bypass -WindowStyle Hidden -File ' + $$q + $$target + $$q; \
		Start-Process powershell.exe -Verb RunAs -WindowStyle Hidden -ArgumentList $$args \
	"

stop:
	@echo "Stopping running server..."
	@$(PS) "\
		$$sq = [char]39; \
		$$killCmd = 'Get-CimInstance Win32_Process | Where-Object { $$_.ProcessId -ne $$PID -and $$_.CommandLine -match ' + $$sq + '$(SCRIPT_NAME)' + $$sq + ' } | Invoke-CimMethod -MethodName Terminate'; \
		Start-Process powershell.exe -Verb RunAs -WindowStyle Hidden -ArgumentList @('-Command', $$killCmd) \
	"

status:
	@$(PS) "\
		$$proc = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $$_.ProcessId -ne $$PID -and $$_.CommandLine -match '$(SCRIPT_NAME)' }; \
		$$port = Get-NetTCPConnection -LocalPort $(PORT) -State Listen -ErrorAction SilentlyContinue; \
		if ($$proc) { \
			Write-Host ('Server status: RUNNING (PID: ' + $$proc.ProcessId + ')') -ForegroundColor Green; \
		} elseif ($$port) { \
			Write-Host 'Server status: RUNNING AS ADMIN (Port $(PORT) is actively listening)' -ForegroundColor Green; \
		} else { \
			Write-Host 'Server status: STOPPED (Or check UAC permissions)' -ForegroundColor Red; \
		} \
	"