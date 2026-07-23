# KrishiIQ — start backend + frontend (run from project root)
$root = $PSScriptRoot

Write-Host "Starting KrishiIQ API on http://127.0.0.1:8001 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001"

Start-Sleep -Seconds 3

Write-Host "Starting web dashboard on http://localhost:5173 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\web-dashboard'; npm run dev"

Write-Host ""
Write-Host "Backend:  http://127.0.0.1:8001/docs"
Write-Host "Frontend: http://localhost:5173"
Write-Host "Login:    officer 9000000001 / officer123"
