# Windows 11 PowerShell setup
Install Python 3.12 and a Java 17 JDK. For example, if winget is available:
```powershell
winget install --exact --id Python.Python.3.12
winget install --exact --id EclipseAdoptium.Temurin.17.JDK
```
Reopen PowerShell, extract the ZIP, then:
```powershell
cd C:\path\SupplySight-Analytics
java -version
py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:SPARK_LOCAL_IP = '127.0.0.1'
$env:PYSPARK_PYTHON = (Get-Command python).Source
python -m supplysight.cli
python -m pytest -q
ruff check src scripts tests notebooks
ruff format --check src scripts tests notebooks
```
If activation is blocked, use `.\.venv\Scripts\python.exe` directly in place of
python. Ensure JAVA_HOME points to the installed JDK root if Spark cannot find Java.
Use a local path without spaces if Hadoop path handling fails on Windows. Spark
may require Windows Hadoop native binaries for file permissions in some installations.
Do not download arbitrary winutils executables. Use WSL2 Ubuntu with Java 17/Python
3.12 as the reliable fallback, or a trusted matching Hadoop build from your institution.
Only Linux was executed here; native Windows runtime remains unverified.

Open the included Excel file. It already contains cached computed values. After
rerunning the pipeline, refresh it with Excel installed:
```powershell
powershell -File .\scripts\Refresh-Workbook.ps1
```
That COM script is authored but not executed here. Close the workbook before running.
It checks row counts before updating and preserves formulas. For full data refresh
without Desktop, request regeneration through the included Artifact Tool builder.
