# Remove Git's usr/bin from PATH to avoid link.exe conflict
$env:PATH = ($env:PATH -split ';' | Where-Object { $_ -notlike '*Git\usr\bin*' }) -join ';'

# Ensure Cargo is in PATH
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"

# Run cargo with all arguments
& cargo @args
