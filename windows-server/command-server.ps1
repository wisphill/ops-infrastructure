$port = 41020

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://+:${port}/")

try {
    $listener.Start()

    Write-Host "Server is running at http://localhost:${port}/ ..." -ForegroundColor Green
    Write-Host "Press Ctrl + C to stop the server." -ForegroundColor Yellow

    while ($true) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response

        $reader = New-Object System.IO.StreamReader($request.InputStream)
        $cmd = $reader.ReadToEnd()
        $reader.Dispose()

        if (-not [string]::IsNullOrWhiteSpace($cmd)) {
            try {
                $psi = New-Object System.Diagnostics.ProcessStartInfo
                $psi.FileName = "powershell.exe"
                $psi.Arguments = "-NoProfile -NonInteractive -Command `"$cmd`""
                $psi.UseShellExecute = $false
                $psi.CreateNoWindow = $true
                $psi.RedirectStandardOutput = $true

                $process = New-Object System.Diagnostics.Process
                $process.StartInfo = $psi
                $process.Start() | Out-Null

                $output = New-Object System.IO.MemoryStream
                $process.StandardOutput.BaseStream.CopyTo($output)
                $process.WaitForExit()

                $buffer = $output.ToArray()

                $output.Dispose()
                $process.Dispose()
            }
            catch {
                $buffer = [System.Text.Encoding]::Default.GetBytes($_.Exception.Message)
            }
        }
        else {
            $buffer = [System.Text.Encoding]::Default.GetBytes("No command provided.")
        }

        $response.ContentLength64 = $buffer.Length
        $response.OutputStream.Write($buffer, 0, $buffer.Length)
        $response.Close()
    }
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    $listener.Stop()
}