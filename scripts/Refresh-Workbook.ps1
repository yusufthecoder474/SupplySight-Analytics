param([string]$ProjectRoot = (Split-Path $PSScriptRoot -Parent))
$ErrorActionPreference = 'Stop'
$payload = Get-Content (Join-Path $ProjectRoot 'reports/workbook_data.json') -Raw | ConvertFrom-Json
$file = Join-Path $ProjectRoot 'excel/SupplySight_Operations_Analysis.xlsx'
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$book = $null
try {
    $book = $excel.Workbooks.Open($file)
    foreach ($name in @('Product Master','Demand History','Forecast Results','Inventory Risk','KPI Validation','Data Dictionary')) {
        $sheet = $book.Worksheets.Item($name)
        $table = $payload.$name
        if ($sheet.ListObjects.Item(1).DataBodyRange.Rows.Count -ne $table.rows.Count) {
            throw "Row count changed for $name. Template is for 20 products / 365 days. Rebuild workbook rather than truncate data."
        }
        for ($i=0; $i -lt $table.rows.Count; $i++) {
            for ($j=0; $j -lt $table.columns.Count; $j++) {
                # Preserve workbook calculations. Refresh owning input columns only.
                if ($name -eq 'Inventory Risk' -and $j -ge 8 -and $j -le 13) { continue }
                if ($name -eq 'Forecast Results' -and $j -ge 7) { continue }
                if ($name -eq 'KPI Validation' -and $j -ge 3) { continue }
                $value = $table.rows[$i][$j]
                if ($null -ne $value -and $table.columns[$j] -in @('date','as_of','train_end')) {
                    $value = ([DateTime]::Parse($value)).ToOADate()
                }
                $sheet.Cells.Item($i+6,$j+1).Value2 = $value
            }
        }
    }
    $excel.CalculateFullRebuild()
    $book.Save()
    Write-Output "Refreshed and saved $file using Excel Desktop. Check KPI Validation and input assumptions."
} finally {
    if ($null -ne $book) { $book.Close($false) }
    $excel.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
}

