@echo off
REM Remove Git's usr/bin from PATH to avoid link.exe conflict
set "PATH=%PATH:C:\Program Files\Git\usr\bin;=%"
set "PATH=%PATH:C:\Program Files\Git\usr\bin=%"

REM Add Cargo to PATH
set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"

REM Run cargo
cargo %*
