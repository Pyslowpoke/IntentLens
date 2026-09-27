param([switch]$Stop)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$fixtureLink=Join-Path $env:LOCALAPPDATA 'workbench-v1-fixture'
# Only this task's synthetic fixture directory is selected.
if (-not (Test-Path -LiteralPath $fixtureLink)) { New-Item -ItemType Junction -Path $fixtureLink -Target (Join-Path $projectRoot '.local') | Out-Null }
$pgBin=Join-Path $fixtureLink 'postgres/pgsql/bin'
$mysqlBin=Join-Path $fixtureLink 'mysql/mysql-8.4.11-winx64/bin'
if ($Stop) {
  & "$pgBin/pg_ctl.exe" -D "$fixtureLink/pg-data" stop
  & "$mysqlBin/mysqladmin.exe" --host=127.0.0.1 --port=53306 --user=root --password=fixture_admin_only shutdown
  exit
}
if (-not (Test-Path "$pgBin/postgres.exe") -or -not (Test-Path "$mysqlBin/mysqld.exe")) { throw 'Download and extract official portable binaries under .local first; see docs/VERIFICATION.md.' }
& "$pgBin/pg_ctl.exe" -D "$fixtureLink/pg-data" -l "$fixtureLink/pg.log" -o '-p 55432 -h 127.0.0.1' start
Start-Process -FilePath "$mysqlBin/mysqld.exe" -ArgumentList '--console',"--basedir=$fixtureLink/mysql/mysql-8.4.11-winx64", "--datadir=$fixtureLink/mysql-data",'--port=53306','--bind-address=127.0.0.1','--mysqlx=OFF','--local-infile=OFF','--secure-file-priv=NULL' -WindowStyle Hidden -RedirectStandardOutput "$fixtureLink/mysql-out.log" -RedirectStandardError "$fixtureLink/mysql-error.log"
Write-Host 'Synthetic PostgreSQL :55432 and MySQL :53306 started on loopback. Use -Stop to stop.'
