@echo off
start "" "wt.exe" nt cmd /k "cd /d D:\Redis\redis-windows-8.10.2 && redis-server.exe"; ^
    nt cmd /k "cd /d D:\vscode\fishmo && .venv\Scripts\python.exe app\main.py";^
    nt cmd /k "cd /d D:\vscode\fishmo\web && npm run dev";^
    nt cmd /k "cd /d D:\vscode\fishmo\admin && npm run dev";


rem nt cmd /k "cd /d D:\vscode\Demo && call claude code"


