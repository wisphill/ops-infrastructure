PS = powershell.exe -NoProfile -ExecutionPolicy Bypass -Command
APP_NAME = WindowsCommandServer
SCRIPT_NAME = command-server.ps1
PORT = 41020

.PHONY: install uninstall start stop status

install:
	@echo "Installing $(SCRIPT_NAME) as a SYSTEM background task..."
	@$(PS) "\
		$$dir = $$env:ProgramData + '\$(APP_NAME)'; \
		if (!(Test-Path $$dir)) { New-Item -ItemType Directory -Path $$dir | Out-Null }; \
		$$target = $$dir + '\$(SCRIPT_NAME)'; \
		Copy-Item -Path '.\$(SCRIPT_NAME)' -Destination $$target -Force; \
		$$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ' + [char]34 + $$target + [char]34); \
		$$trigger = New-ScheduledTaskTrigger -AtStartup; \
		$$principal = New-ScheduledTaskPrincipal -UserId 'NT AUTHORITY\SYSTEM' -LogonType ServiceAccount -RunLevel Highest; \
		Register-ScheduledTask -TaskName '$(APP_NAME)' -Action $$action -Trigger $$trigger -Principal $$principal -Force | Out-Null; \
		Write-Host '[OK] Installed successfully to:' $$dir -ForegroundColor Green; \
		Write-Host '[OK] Scheduled Task created. Server will start on boot WITHOUT login or UAC.' -ForegroundColor Green \
	"

uninstall:
	@echo "Uninstalling $(APP_NAME)..."
	@$(PS) "\
		$$dir = $$env:ProgramData + '\$(APP_NAME)'; \
		Unregister-ScheduledTask -TaskName '$(APP_NAME)' -Confirm:$$false -ErrorAction SilentlyContinue; \
		$$sq = [char]39; \
		$$killCmd = 'Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $$_.ProcessId -ne $$PID -and $$_.CommandLine -match ' + $$sq + '$(SCRIPT_NAME)' + $$sq + ' } | Invoke-CimMethod -MethodName Terminate'; \
		Invoke-Expression $$killCmd; \
		Start-Sleep -Seconds 2; \
		if (Test-Path $$dir) { Remove-Item -Recurse -Force $$dir }; \
		Write-Host '[OK] Task unregistered and files cleaned up successfully.' -ForegroundColor Yellow \
	"

start:
	@echo "Starting $(APP_NAME) via Task Scheduler..."
	@$(PS) "\
		Start-ScheduledTask -TaskName '$(APP_NAME)' -ErrorAction SilentlyContinue; \
		Write-Host '[OK] Server started in background.' -ForegroundColor Green \
	"

stop:
	@echo "Stopping $(APP_NAME)..."
	@$(PS) "\
		Stop-ScheduledTask -TaskName '$(APP_NAME)' -ErrorAction SilentlyContinue; \
		$$sq = [char]39; \
		$$killCmd = 'Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $$_.ProcessId -ne $$PID -and $$_.CommandLine -match ' + $$sq + '$(SCRIPT_NAME)' + $$sq + ' } | Invoke-CimMethod -MethodName Terminate'; \
		Invoke-Expression $$killCmd; \
		Write-Host '[OK] Server stopped.' -ForegroundColor Yellow \
	"

status:
	@$(PS) "\
		$$task = Get-ScheduledTask -TaskName '$(APP_NAME)' -ErrorAction SilentlyContinue; \
		$$proc = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $$_.ProcessId -ne $$PID -and $$_.CommandLine -match '$(SCRIPT_NAME)' }; \
		$$port = Get-NetTCPConnection -LocalPort $(PORT) -State Listen -ErrorAction SilentlyContinue; \
		if ($$task) { Write-Host 'Task Scheduler State :' $$task.State -ForegroundColor Cyan } else { Write-Host 'Task Scheduler State : Not Installed' -ForegroundColor Gray }; \
		if ($$proc) { \
			Write-Host ('Server Process       : RUNNING (PID: ' + $$proc.ProcessId + ')') -ForegroundColor Green; \
		} elseif ($$port) { \
			Write-Host 'Server Port          : RUNNING (Port $(PORT) is listening)' -ForegroundColor Green; \
		} else { \
			Write-Host 'Server Process       : STOPPED' -ForegroundColor Red; \
		} \
	"