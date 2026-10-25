# Ortam kontrolü: JDK 21, Ghidra, REA, Python paketleri ve GPower.exe SHA-256
param(
    [string]$GPowerExe = "",
    [string]$GhidraDir = $env:GHIDRA_INSTALL_DIR
)

function Report($name, $ok, $detail) {
    $mark = if ($ok) { "[OK]  " } else { "[EKSIK]" }
    Write-Output ("{0} {1,-12} {2}" -f $mark, $name, $detail)
}

# JDK: Ghidra 11.x için 21 gerekir
$javaVer = ""
try { $javaVer = (& java -version 2>&1 | Select-Object -First 1).ToString() } catch {}
Report "JDK 21" ($javaVer -match '"21') $javaVer

# Ghidra
$ghidraOk = $GhidraDir -and (Test-Path (Join-Path $GhidraDir "ghidraRun.bat"))
Report "Ghidra" $ghidraOk ($(if ($GhidraDir) { $GhidraDir } else { "GHIDRA_INSTALL_DIR tanimli degil" }))

# REA (yalnizca npm'deki rea-agents paketi)
$reaVer = ""
try { $reaVer = (& npm ls -g rea-agents --depth=0 2>$null | Select-String "rea-agents").ToString().Trim() } catch {}
Report "rea-agents" ([bool]$reaVer) ($(if ($reaVer) { $reaVer } else { "npx rea-agents setup calistirin" }))

# Python paketleri
foreach ($pkg in "scipy", "statsmodels", "pytest") {
    $v = & python -c "import $pkg; print($pkg.__version__)" 2>$null
    Report $pkg ([bool]$v) $v
}

# GPower.exe hash (README'ye yazilir; exe repoya konmaz)
if ($GPowerExe) {
    if (Test-Path -LiteralPath $GPowerExe) {
        $h = (Get-FileHash -LiteralPath $GPowerExe -Algorithm SHA256).Hash.ToLower()
        Report "GPower.exe" $true "SHA-256 $h"
    } else {
        Report "GPower.exe" $false "bulunamadi: $GPowerExe"
    }
} else {
    Report "GPower.exe" $false "-GPowerExe <yol> verin"
}
