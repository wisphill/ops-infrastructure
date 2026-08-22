PS = powershell.exe -NoProfile -ExecutionPolicy Bypass -Command
APP_NAME = WindowsCommandServer
SCRIPT_NAME = command-server.ps1

.PHONY: install uninstall start stop status

install:
	@echo "Installing $(SCRIPT_NAME) and setting up autostart..."
	@$(PS) "\
		$$dir = \"$$env:APPDATA\$(APP_NAME)\"; \
		if (!(Test-Path $$dir)) { New-Item -ItemType Directory -Path $$dir | Out-Null }; \
		Copy-Item -Path '.\$(SCRIPT_NAME)' -Destination \"$$dir\$(SCRIPT_NAME)\" -Force; \
		$$cmd = \"powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File `\"$$dir\$(SCRIPT_NAME)`\"\"; \
		Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name '$(APP_NAME)' -Value $$cmd; \
		Write-Host '[OK] Installed successfully to:' $$dir -ForegroundColor Green; \
		Write-Host '[OK] Added to Windows Startup (Registry HKCU).' -ForegroundColor Green \
	"

uninstall:
	@echo "Uninstalling $(APP_NAME)..."
	@$(PS) "\
		$$dir = \"$$env:APPDATA\$(APP_NAME)\"; \
		Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name '$(APP_NAME)' -ErrorAction SilentlyContinue; \
		Get-CimInstance Win32_Process | Where-Object { $$_.ProcessId -ne $$PID -and $$_.CommandLine -like '*$(SCRIPT_NAME)*' } | Stop-Process -Force; \
		if (Test-Path $$dir) { Remove-Item -Recurse -Force $$dir }; \
		Write-Host '[OK] Uninstalled and cleaned up successfully.' -ForegroundColor Yellow \
	"

start:
	@echo "Starting $(APP_NAME) in background..."
	@$(PS) "Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-ExecutionPolicy', 'Bypass', '-File', \"$$env:APPDATA\$(APP_NAME)\$(SCRIPT_NAME)\""

stop:
	@echo "Stopping running server..."
	@$(PS) "Get-CimInstance Win32_Process -Filter \"CommandLine LIKE '%$(SCRIPT_NAME)%' AND ProcessId <> $$PID\" | ForEach-Object { Stop-Process -Id $$_.ProcessId -Force }"
	
status:
	@$(PS) "\
		$$proc = Get-CimInstance Win32_Process -Filter \"CommandLine LIKE '%$(SCRIPT_NAME)%' AND ProcessId <> $$PID\"; \
		if ($$proc) { Write-Host 'Server status: RUNNING (PID:' $$proc.ProcessId ')' -ForegroundColor Green } \
		else { Write-Host 'Server status: STOPPED' -ForegroundColor Red } \
	"