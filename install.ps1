# Ensures the script runs as Administrator
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process PowerShell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host "============================================="
Write-Host "      Wallet Hub Secure MSIX Installer       "
Write-Host "============================================="
Write-Host ""
Write-Host "1/4 Creating a secure Self-Signed Certificate..."
$cert = New-SelfSignedCjertificate -Type Custom -Subject "CN=WalletHub" -KeyUsage DigitalSignature -FriendlyName "Wallet Hub App Cert" -CertStoreLocation "Cert:\LocalMachine\My" -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")

$certPath = "$PSScriptRoot\WalletHub.cer"
Export-Certificate -cert $cert -FilePath $certPath -Force | Out-Null

Write-Host "2/4 Adding the Certificate to your Trusted Root..."
Import-Certificate -FilePath $certPath -CertStoreLocation Cert:\LocalMachine\Root | Out-Null

Write-Host "3/4 Digitally Signing the WalletHub.msix package..."
$signtool = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe"
$msixPath = "$PSScriptRoot\WalletHub.msix"

if (Test-Path $signtool) {
    # Sign using the certificate that is now in the LocalMachine store 
    # (avoiding any annoying password or file-export popups!)
    & $signtool sign /fd SHA256 /a /sha1 $($cert.Thumbprint) "$msixPath" | Out-Null
} else {
    Write-Host "Warning: Windows SDK signtool not found. Assuming package is already signed." -ForegroundColor Yellow
}

Write-Host "4/4 Installing Wallet Hub to your PC..."
Add-AppxPackage -Path "$msixPath" -ForceApplicationShutdown

Write-Host ""
Write-Host "============================================="
Write-Host "   ✅ INSTALLATION COMPLETE! ✅ "
Write-Host "  Wallet Hub is now installed securely on "
Write-Host "  your system. Find it in your Start Menu!"
Write-Host "============================================="
Write-Host ""
Write-Host "Press any key to close this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
