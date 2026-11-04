# Second Brain Kit - Windows tek komut kurulum.
# Tek satir (PowerShell):  irm https://raw.githubusercontent.com/<hesap>/second-brain-kit/main/install.ps1 | iex
#   Varsayilan: son Release'ten "Second Brain Setup.exe" Masaustune indirilir ve calistirilir (sihirbaz acilir).
#   Depo gizli oldugu icin once `gh` CLI (gh auth login), yoksa GITHUB_TOKEN / SB_GH_TOKEN ile API kullanilir.
#   Ikisi de yoksa nasil yapilacagi yazilir ve kaynak koddan kurulum (uv + setup/app.py) denenir.
# Kaynak koddan panel:     powershell -ExecutionPolicy Bypass -File install.ps1 --source
# Eski soru-cevap kurucu:  powershell -ExecutionPolicy Bypass -File install.ps1 --cli  (ya da install.py argumanlari: --yes, --answers ...)
# Ortam: SB_REPO (varsayilan Cullinan-coder/second-brain-kit), SB_GH_TOKEN/GITHUB_TOKEN, SB_REPO_ZIP, SB_REPO_GIT, SB_DIR (kaynak indirme klasoru, varsayilan ~\SecondBrainKit)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$repo = if ($env:SB_REPO) { $env:SB_REPO } else { "Cullinan-coder/second-brain-kit" }
$assetPattern = "Second-Brain-Setup*.exe"
$wantCli = $args -contains "--cli"
$wantSource = $args -contains "--source"
$rest = @($args | Where-Object { $_ -ne "--cli" -and $_ -ne "--source" })

function Get-SetupFromRelease {
    # Basarili olursa indirilen exe yolunu dondurur, olmazsa $null.
    $tmp = Join-Path $env:TEMP "sb-setup-dl"
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
    New-Item -ItemType Directory -Force $tmp | Out-Null
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        Write-Host "gh CLI ile son surum indiriliyor ($repo)..."
        try {
            gh release download --repo $repo --pattern $assetPattern --pattern "SHA256SUMS" --dir $tmp --clobber
            $f = Get-ChildItem $tmp -Filter "Second-Brain-Setup*.exe" | Select-Object -First 1
            if ($f) { return $f.FullName }
        } catch { Write-Host "gh ile indirilemedi: $($_.Exception.Message)" }
    }
    $token = if ($env:SB_GH_TOKEN) { $env:SB_GH_TOKEN } else { $env:GITHUB_TOKEN }
    if ($token) {
        Write-Host "GitHub API ile son surum indiriliyor ($repo)..."
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            $h = @{ Authorization = "Bearer $token"; Accept = "application/vnd.github+json"; "User-Agent" = "second-brain-installer" }
            $rel = Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/releases/latest" -Headers $h
            $asset = $rel.assets | Where-Object { $_.name -like $assetPattern } | Select-Object -First 1
            if ($asset) {
                $out = Join-Path $tmp $asset.name
                $h2 = @{ Authorization = "Bearer $token"; Accept = "application/octet-stream"; "User-Agent" = "second-brain-installer" }
                Invoke-WebRequest -Uri $asset.url -Headers $h2 -OutFile $out -UseBasicParsing
                $sums = $rel.assets | Where-Object { $_.name -eq "SHA256SUMS" } | Select-Object -First 1
                if ($sums) { Invoke-WebRequest -Uri $sums.url -Headers $h2 -OutFile (Join-Path $tmp "SHA256SUMS") -UseBasicParsing }
                return $out
            }
            Write-Host "Son surumde $assetPattern bulunamadi."
        } catch { Write-Host "API ile indirilemedi: $($_.Exception.Message)" }
    }
    return $null
}

function Test-SetupHash([string]$exe) {
    # Indirilen Setup dosyasini ayni klasordeki SHA256SUMS ile dogrular (D-13). Eslesmezse / ozet yoksa dosyayi SILER ve $false doner.
    $sumsFile = Join-Path (Split-Path $exe -Parent) "SHA256SUMS"
    $name = Split-Path $exe -Leaf
    $want = $null
    if (Test-Path -LiteralPath $sumsFile) {
        foreach ($ln in Get-Content -LiteralPath $sumsFile) {
            if ($ln -match '^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$' -and $Matches[2] -eq $name) { $want = $Matches[1].ToLower() }
        }
    }
    $got = (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash.ToLower()
    if (-not $want -or $got -ne $want) {
        Remove-Item -Force -LiteralPath $exe -ErrorAction SilentlyContinue
        return $false
    }
    return $true
}

if (-not $wantCli -and -not $wantSource -and $rest.Count -eq 0) {
    $exe = Get-SetupFromRelease
    if ($exe) {
        if (-not (Test-SetupHash $exe)) {
            Write-Host "HATA: Setup dosyasinin SHA-256 ozeti surumdeki SHA256SUMS ile eslesmedi (ya da SHA256SUMS yok). Dosya silindi, calistirilmadi."
            exit 1
        }
        Write-Host "SHA-256 dogrulandi."
        $desktop = [Environment]::GetFolderPath("Desktop")
        $dest = Join-Path $desktop "Second Brain Setup.exe"
        Copy-Item -Force $exe $dest
        Write-Host "Masaustune indirildi: $dest"
        Write-Host "Ilk acilista Windows 'Bilinmeyen yayinci' uyarisi cikarsa: Ek bilgi > Yine de calistir (uygulama imzasiz)."
        Start-Process -FilePath $dest
        exit 0
    }
    Write-Host ""
    Write-Host "Setup.exe indirilemedi. Depo gizli oldugu icin giris gerekir. Su yollardan biri:"
    Write-Host "  1) GitHub CLI kur ve giris yap:  winget install GitHub.cli ; gh auth login   (sonra bu komutu yeniden calistir)"
    Write-Host "  2) Kisisel erisim jetonu (repo okuma yetkili) ile:  `$env:SB_GH_TOKEN='ghp_...' ; irm <install.ps1 adresi> | iex"
    Write-Host "  3) Tarayicidan Releases sayfasindan Second-Brain-Setup.exe dosyasini indir: https://github.com/$repo/releases/latest"
    Write-Host "Simdilik kaynak koddan kurulum deneniyor (uv + setup/app.py)..."
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv (Python paket yoneticisi) kuruluyor..."
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Uyari: git yok. 'winget install Git.Git' ile kurman onerilir (geri alma ve yedek icin)."
}
# Repo yoksa (irm | iex ile calistirildi) indir: once git clone, olmazsa zip.
if (-not $root -or -not (Test-Path (Join-Path $root "install.py"))) {
    $dest = if ($env:SB_DIR) { $env:SB_DIR } else { Join-Path $env:USERPROFILE "SecondBrainKit" }
    $gitUrl = if ($env:SB_REPO_GIT) { $env:SB_REPO_GIT } else { "https://github.com/$repo.git" }
    $zipUrl = if ($env:SB_REPO_ZIP) { $env:SB_REPO_ZIP } else { "https://github.com/$repo/archive/refs/heads/main.zip" }
    if (Test-Path (Join-Path $dest "install.py")) {
        Write-Host "Mevcut kit kullaniliyor: $dest"
    } elseif (Get-Command git -ErrorAction SilentlyContinue) {
        git clone --depth 1 $gitUrl $dest
    } else {
        $tmp = Join-Path $env:TEMP "sb-kit.zip"
        Invoke-WebRequest -Uri $zipUrl -OutFile $tmp
        $x = Join-Path $env:TEMP "sb-kit-x"
        if (Test-Path $x) { Remove-Item -Recurse -Force $x }
        Expand-Archive -Path $tmp -DestinationPath $x
        New-Item -ItemType Directory -Force $dest | Out-Null
        Copy-Item -Path (Join-Path (Get-ChildItem $x | Select-Object -First 1).FullName "*") -Destination $dest -Recurse -Force
    }
    $root = $dest
}
Set-Location $root
if ($wantCli -or $rest.Count -gt 0) {
    uv run --no-project --python 3.12 --with pyyaml install.py @rest
} else {
    $sys = @($root, (Join-Path $root "system"), (Join-Path $root "_system")) | Where-Object { Test-Path (Join-Path $_ "setup\app.py") } | Select-Object -First 1
    if (-not $sys) { Write-Error "setup/app.py bulunamadi ($root)"; exit 1 }
    uv run --directory $sys --python 3.12 --with pywebview python setup/app.py
}
