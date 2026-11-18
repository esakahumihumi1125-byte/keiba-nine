# ARC RACE / JRA-VAN Data Lab JV-Link local diagnostics.
# Only checks 64-bit COM registration and JVInit. Does not request race data.
# Never print local settings, subscription identifiers, secrets or provider data.
$ErrorActionPreference = 'Stop'
$exitCode = 1
$jv = $null

try {
    if (-not [Environment]::Is64BitProcess) {
        Write-Output 'JVLINK_CHECK=WRONG_BITNESS'
        Write-Output 'Use 64-bit Windows PowerShell with the installed 64-bit JV-Link.'
        $exitCode = 3
    }
    else {
        try {
            $jv = New-Object -ComObject 'JVDTLab.JVLink'
        }
        catch {
            Write-Output 'JVLINK_CHECK=COM_UNAVAILABLE'
            Write-Output '64-bit JV-Link COM registration could not be opened.'
            $exitCode = 2
        }

        if ($null -ne $jv) {
            # UNKNOWN is the SDK's diagnostic/sample SID. This is not a race
            # download, a subscription status API, or a credential check.
            $result = $jv.JVInit('UNKNOWN')
            if ($result -is [int] -and $result -eq 0) {
                Write-Output 'JVLINK_CHECK=INIT_OK'
                Write-Output 'COM and JVInit succeeded. No official JRA data was read.'
                $exitCode = 0
            }
            else {
                Write-Output 'JVLINK_CHECK=INIT_FAILED'
                if ($result -is [int]) {
                    Write-Output ('JVLINK_INIT_RETURN=' + $result)
                }
                Write-Output 'JV-Link initialized unsuccessfully; data import was not attempted.'
                $exitCode = 4
            }
        }
    }
}
catch {
    Write-Output 'JVLINK_CHECK=INIT_EXCEPTION'
    Write-Output 'Initialization raised an error; check JV-Link settings locally.'
    $exitCode = 5
}
finally {
    if ($null -ne $jv) {
        try {
            [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($jv)
        }
        catch {
            # Cleanup never replaces the already printed diagnostic.
        }
    }
}
exit $exitCode
