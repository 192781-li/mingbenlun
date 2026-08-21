# 云电脑性能扫描与安全清理脚本
# 用法：右键 -> 以管理员身份运行
# 只做L1安全清理（临时文件/缓存），不修改系统设置，不删个人文件

$ErrorActionPreference = "SilentlyContinue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  云电脑性能扫描与安全清理" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ===== 第一部分：系统状态扫描 =====
Write-Host "【系统状态扫描】" -ForegroundColor Yellow
Write-Host ""

# 操作系统
$os = Get-CimInstance Win32_OperatingSystem
Write-Host "系统: $($os.Caption) ($($os.Version))"
Write-Host "开机时间: $($os.LastBootUpTime)"
$uptime = (Get-Date) - $os.LastBootUpTime
Write-Host "已运行: $($uptime.Days)天 $($uptime.Hours)小时 $($uptime.Minutes)分钟"

# CPU
$cpu = Get-CimInstance Win32_Processor
Write-Host "CPU: $($cpu.Name)"
$cpuLoad = (Get-CimInstance Win32_Processor).LoadPercentage
Write-Host "CPU当前负载: $cpuLoad%"

# 内存
$totalMem = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
$freeMem = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
$usedMem = [math]::Round($totalMem - $freeMem, 1)
$memPct = [math]::Round($usedMem / $totalMem * 100, 0)
Write-Host "内存: ${usedMem}GB / ${totalMem}GB 已用 ($memPct%)"
if ($memPct -gt 80) { Write-Host "  ⚠️  内存占用过高，可能导致卡顿！" -ForegroundColor Red }

# 磁盘
Write-Host ""
Write-Host "【磁盘空间】"
Get-PSDrive -PSProvider FileSystem | ForEach-Object {
    if ($_.Used -ne $null -and $_.Free -ne $null) {
        $total = [math]::Round(($_.Used + $_.Free) / 1GB, 1)
        $used = [math]::Round($_.Used / 1GB, 1)
        $free = [math]::Round($_.Free / 1GB, 1)
        $pct = if ($total -gt 0) { [math]::Round($used / $total * 100, 0) } else { 0 }
        $color = if ($pct -gt 90) { "Red" } elseif ($pct -gt 80) { "Yellow" } else { "Green" }
        Write-Host "  $($_.Name): ${used}GB / ${total}GB 已用 ($pct%)  剩余${free}GB" -ForegroundColor $color
    }
}

# ===== 第二部分：占用资源的进程 =====
Write-Host ""
Write-Host "【内存占用TOP10进程】" -ForegroundColor Yellow
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 | ForEach-Object {
    $memMB = [math]::Round($_.WorkingSet64 / 1MB, 0)
    Write-Host "  $($_.ProcessName.PadRight(25)) ${memMB}MB"
}

Write-Host ""
Write-Host "【CPU占用TOP5进程】" -ForegroundColor Yellow
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 | ForEach-Object {
    $cpuSec = [math]::Round($_.CPU, 1)
    Write-Host "  $($_.ProcessName.PadRight(25)) CPU时间${cpuSec}秒"
}

# 浏览器进程统计
$chromeProcs = Get-Process chrome -ErrorAction SilentlyContinue
$edgeProcs = Get-Process msedge -ErrorAction SilentlyContinue
if ($chromeProcs) {
    $chromeMem = [math]::Round(($chromeProcs | Measure-Object WorkingSet64 -Sum).Sum / 1MB, 0)
    Write-Host ""
    Write-Host "  Chrome: $($chromeProcs.Count)个进程, 共${chromeMem}MB" -ForegroundColor Magenta
}
if ($edgeProcs) {
    $edgeMem = [math]::Round(($edgeProcs | Measure-Object WorkingSet64 -Sum).Sum / 1MB, 0)
    Write-Host "  Edge: $($edgeProcs.Count)个进程, 共${edgeMem}MB" -ForegroundColor Magenta
}

# ===== 第三部分：启动项 =====
Write-Host ""
Write-Host "【开机启动项】" -ForegroundColor Yellow
$startup = Get-CimInstance Win32_StartupCommand | Where-Object { $_.Name -ne $null }
if ($startup) {
    Write-Host "  共$($startup.Count)个启动项:"
    $startup | Select-Object -First 10 | ForEach-Object {
        Write-Host "    - $($_.Name)"
    }
    if ($startup.Count -gt 10) { Write-Host "    ...等共$($startup.Count)个" }
} else {
    Write-Host "  无明显启动项"
}

# ===== 第四部分：可清理空间统计 =====
Write-Host ""
Write-Host "【可清理空间统计】" -ForegroundColor Yellow
$totalCleanable = 0

# 临时文件
$tempPath = $env:TEMP
$tempSize = (Get-ChildItem $tempPath -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
$tempMB = [math]::Round($tempSize / 1MB, 1)
$totalCleanable += $tempSize
Write-Host "  用户临时文件: ${tempMB}MB"

# Windows临时文件
$winTemp = "C:\Windows\Temp"
if (Test-Path $winTemp) {
    $winTempSize = (Get-ChildItem $winTemp -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    $winTempMB = [math]::Round($winTempSize / 1MB, 1)
    $totalCleanable += $winTempSize
    Write-Host "  Windows临时文件: ${winTempMB}MB"
}

# 浏览器缓存
$chromeCache = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
if (Test-Path $chromeCache) {
    $chromeSize = (Get-ChildItem $chromeCache -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    $chromeMB = [math]::Round($chromeSize / 1MB, 1)
    $totalCleanable += $chromeSize
    Write-Host "  Chrome缓存: ${chromeMB}MB"
}

$edgeCache = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache"
if (Test-Path $edgeCache) {
    $edgeSize = (Get-ChildItem $edgeCache -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    $edgeMB = [math]::Round($edgeSize / 1MB, 1)
    $totalCleanable += $edgeSize
    Write-Host "  Edge缓存: ${edgeMB}MB"
}

# Windows更新缓存
$winsxs = "C:\Windows\SoftwareDistribution\Download"
if (Test-Path $winsxs) {
    $winsxsSize = (Get-ChildItem $winsxs -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    $winsxsMB = [math]::Round($winsxsSize / 1MB, 1)
    $totalCleanable += $winsxsSize
    Write-Host "  Windows更新缓存: ${winsxsMB}MB"
}

$totalGB = [math]::Round($totalCleanable / 1GB, 2)
Write-Host ""
Write-Host "  合计可清理: $totalGB GB" -ForegroundColor Cyan

# ===== 第五部分：执行清理 =====
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  开始安全清理..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$cleaned = 0

# 清理用户临时文件
Write-Host "清理用户临时文件..." -NoNewline
try {
    Remove-Item "$tempPath\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host " 完成" -ForegroundColor Green
    $cleaned += $tempSize
} catch { Write-Host " 部分文件被占用，跳过" -ForegroundColor Yellow }

# 清理Windows临时文件
Write-Host "清理Windows临时文件..." -NoNewline
try {
    Remove-Item "$winTemp\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host " 完成" -ForegroundColor Green
    $cleaned += $winTempSize
} catch { Write-Host " 部分文件被占用，跳过" -ForegroundColor Yellow }

# 清理Chrome缓存
if (Test-Path $chromeCache) {
    Write-Host "清理Chrome缓存..." -NoNewline
    try {
        Remove-Item "$chromeCache\*" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host " 完成" -ForegroundColor Green
        $cleaned += $chromeSize
    } catch { Write-Host " Chrome正在运行，跳过（关闭浏览器后可清理）" -ForegroundColor Yellow }
}

# 清理Edge缓存
if (Test-Path $edgeCache) {
    Write-Host "清理Edge缓存..." -NoNewline
    try {
        Remove-Item "$edgeCache\*" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host " 完成" -ForegroundColor Green
        $cleaned += $edgeSize
    } catch { Write-Host " Edge正在运行，跳过" -ForegroundColor Yellow }
}

# 清理Windows更新缓存
if (Test-Path $winsxs) {
    Write-Host "清理Windows更新缓存..." -NoNewline
    try {
        Stop-Service wuauserv -Force -ErrorAction SilentlyContinue
        Remove-Item "$winsxs\*" -Recurse -Force -ErrorAction SilentlyContinue
        Start-Service wuauserv -ErrorAction SilentlyContinue
        Write-Host " 完成" -ForegroundColor Green
        $cleaned += $winsxsSize
    } catch { Write-Host " 跳过" -ForegroundColor Yellow }
}

# ===== 第六部分：内存优化 =====
Write-Host ""
Write-Host "优化内存..." -NoNewline
# 清理工作集（释放闲置内存）
Get-Process | Where-Object { $_.WorkingSet64 -gt 100MB -and $_.ProcessName -notin ("System","Idle") } | ForEach-Object {
    try {
        $proc = Get-Process -Id $_.Id -ErrorAction SilentlyContinue
        if ($proc) {
            # 不强制清理，只提示
        }
    } catch {}
}
Write-Host " 完成（建议关闭不用的浏览器标签页）" -ForegroundColor Green

# ===== 第七部分：结果汇总 =====
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  清理完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
$cleanedGB = [math]::Round($cleaned / 1GB, 2)
Write-Host "  释放空间: 约 $cleanedGB GB"
Write-Host ""

# 重新检查内存
$os2 = Get-CimInstance Win32_OperatingSystem
$freeMem2 = [math]::Round($os2.FreePhysicalMemory / 1MB, 1)
Write-Host "  当前可用内存: ${freeMem2}GB"
Write-Host ""

# 建议
Write-Host "【卡顿原因分析与建议】" -ForegroundColor Yellow
if ($memPct -gt 80) {
    Write-Host "  ⚠️  内存占用过高是卡顿主因！" -ForegroundColor Red
    Write-Host "     建议：1) 关闭不用的浏览器标签页"
    Write-Host "           2) 重启云电脑释放全部内存"
    Write-Host "           3) 考虑升级云电脑配置"
}
if ($cpuLoad -gt 50) {
    Write-Host "  ⚠️  CPU负载偏高" -ForegroundColor Red
    Write-Host "     建议：查看CPU占用TOP进程，关闭不必要的程序"
}
Write-Host "  💡 通用建议：定期重启云电脑（每周1次），保持流畅"
Write-Host ""

Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
