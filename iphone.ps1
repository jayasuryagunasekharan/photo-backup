$shell = New-Object -ComObject Shell.Application

$thisPC = $shell.Namespace(17)

$iphone = $thisPC.Items() | Where-Object { $_.Name -like "*iPhone*" }

$internal = $iphone.GetFolder.Items() |
            Where-Object { $_.Name -eq "Internal Storage" }

$dest = "C:\IphoneBackUp"
New-Item -ItemType Directory -Force -Path $dest

# Copy EVERYTHING under Internal Storage
foreach ($item in $internal.GetFolder.Items()) {
    $shell.Namespace($dest).CopyHere($item, 16)
}
