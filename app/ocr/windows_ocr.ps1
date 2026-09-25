# OCR with the engine built into Windows 10/11 (Windows.Media.Ocr), called by app/ocr/windows_ocr.py (DECISIONS D55).
# Input (stdin): one JSON object per line: {"page": <int>, "png": "<base64 PNG>"}. Images stay in memory.
# Output (stdout, UTF-8 JSON): [{"page", "width", "height", "lines": [{"text", "x0", "x1", "top", "height"}]}]
param([string]$Lang = "en-US")
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Foundation, ContentType = WindowsRuntime]

$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq "AsTask" -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq "IAsyncOperation``1"
} | Select-Object -First 1
function Await($operation, [Type]$type) {
  $task = $asTask.MakeGenericMethod($type).Invoke($null, @($operation))
  $null = $task.Wait(-1)
  $task.Result
}

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new($Lang))
if ($null -eq $engine) { [Console]::Error.WriteLine("no Windows OCR engine for $Lang"); exit 2 }

$pages = New-Object System.Collections.Generic.List[object]
while ($null -ne ($raw = [Console]::In.ReadLine())) {
  if (-not $raw.Trim()) { continue }
  $item = $raw | ConvertFrom-Json
  $bytes = [Convert]::FromBase64String($item.png)
  $memory = New-Object System.IO.MemoryStream(, $bytes)
  $stream = [System.IO.WindowsRuntimeStreamExtensions]::AsRandomAccessStream($memory)
  $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
  $lines = New-Object System.Collections.Generic.List[object]
  foreach ($line in $result.Lines) {
    $rects = @($line.Words | ForEach-Object { $_.BoundingRect })
    if ($rects.Count -eq 0) { continue }
    $x0 = ($rects | ForEach-Object { $_.X } | Measure-Object -Minimum).Minimum
    $x1 = ($rects | ForEach-Object { $_.X + $_.Width } | Measure-Object -Maximum).Maximum
    $top = ($rects | ForEach-Object { $_.Y } | Measure-Object -Minimum).Minimum
    $height = ($rects | ForEach-Object { $_.Height } | Measure-Object -Maximum).Maximum
    $lines.Add([ordered]@{ text = $line.Text; x0 = $x0; x1 = $x1; top = $top; height = $height })
  }
  $pages.Add([ordered]@{ page = [int]$item.page; width = $bitmap.PixelWidth; height = $bitmap.PixelHeight; lines = $lines.ToArray() })
  $bitmap.Dispose(); $stream.Dispose(); $memory.Dispose()
}
[Console]::Out.Write((ConvertTo-Json -InputObject $pages.ToArray() -Depth 6 -Compress))
