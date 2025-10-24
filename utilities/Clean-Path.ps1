param(
  [switch]$User,
  [switch]$Machine,
  [switch]$All,
  [string]$KeepRegex
)

# default: User
if(-not ($User -or $Machine -or $All)){ $User = $true }
if($All){ $User = $true; $Machine = $true }

function Is-Admin {
  try {
    $wi=[Security.Principal.WindowsIdentity]::GetCurrent()
    (New-Object Security.Principal.WindowsPrincipal $wi).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch { $false }
}

function Clean([string]$scope){
  $orig = [Environment]::GetEnvironmentVariable('Path',$scope); if($null -eq $orig){ $orig='' }
  $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
  $kept = New-Object 'System.Collections.Generic.List[string]'
  $removed = 0

  foreach($e in ($orig -split ';')){
    if([string]::IsNullOrWhiteSpace($e)){ continue }
    $t = $e.Trim().Trim('"').TrimEnd('\','/')
    $exp = [Environment]::ExpandEnvironmentVariables($t)
    $keep = ($KeepRegex -and $t -match $KeepRegex) -or (Test-Path -LiteralPath $exp -PathType Container)
    if($keep){
      if(($t -ne '') -and $seen.Add($t)){ [void]$kept.Add($t) } else { $removed++ }
    } else { $removed++ }
  }

  $new = ($kept -join ';')
  [Environment]::SetEnvironmentVariable('Path',$new,$scope)
  "{0,-8} kept: {1}  removed: {2}" -f "[$scope]", $kept.Count, $removed
}

if($Machine -and -not (Is-Admin)){ Write-Warning "Machine PATH needs an elevated PowerShell (Run as Administrator)." }

if($User){    Write-Host (Clean 'User') }
if($Machine){ Write-Host (Clean 'Machine') }
