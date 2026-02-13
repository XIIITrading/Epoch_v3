# DOW AI Trading Assistant Launcher
# Epoch Trading System v1 - XIII Trading LLC

$Host.UI.RawUI.WindowTitle = "DOW AI Trading Assistant"
Set-Location "C:\XIIITradingSystems\Epoch\04_dow_ai"

function Show-Menu {
    Clear-Host
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   DOW AI TRADING ASSISTANT" -ForegroundColor Yellow
    Write-Host "   Epoch Trading System v1" -ForegroundColor DarkGray
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "  entry [TICKER] [long/short] [MODEL]" -ForegroundColor Green
    Write-Host "  exit [TICKER] [sell/cover] [MODEL]" -ForegroundColor Green
    Write-Host "  models (list available models)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Add --datetime `"YYYY-MM-DD HH:MM`" for backtest" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Models: EPCH_01, EPCH_02, EPCH_03, EPCH_04" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Type 'quit' to exit" -ForegroundColor DarkGray
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

while ($true) {
    Show-Menu
    $userInput = Read-Host "dow"

    if ($userInput -eq "quit" -or $userInput -eq "exit" -or $userInput -eq "q") {
        Write-Host ""
        Write-Host "Goodbye!" -ForegroundColor Green
        Start-Sleep -Seconds 2
        break
    }

    if ($userInput -ne "") {
        Write-Host ""
        Write-Host "Running analysis..." -ForegroundColor Yellow
        Write-Host ""

        # Split input into arguments and run
        $args = $userInput -split " "
        & python main.py @args

        Write-Host ""
        Read-Host "Press Enter to continue"
    }
}
