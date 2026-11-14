@echo off
cd /d "%~dp0"
echo ============================================================
echo  Un Jour a Giverny - Lossless 1080p MP4 Reassembly (Windows)
echo ============================================================
echo.
echo Note: monet_un_jour_a_giverny_720p.mp4 is already a complete single MP4.
echo.

if exist "monet_un_jour_a_giverny_1080p.mp4.part.00" (
  echo Merging 1080p MP4 (5 chunks)...
  copy /b "monet_un_jour_a_giverny_1080p.mp4.part.00"+"monet_un_jour_a_giverny_1080p.mp4.part.01"+"monet_un_jour_a_giverny_1080p.mp4.part.02"+"monet_un_jour_a_giverny_1080p.mp4.part.03"+"monet_un_jour_a_giverny_1080p.mp4.part.04" "monet_un_jour_a_giverny_1080p.mp4" >nul
  if exist "monet_un_jour_a_giverny_1080p.mp4" (
    echo       OK: monet_un_jour_a_giverny_1080p.mp4 ready!
  ) else (
    echo       FAILED: 1080p merge failed.
  )
) else (
  echo Skipped 1080p (chunks not found in this folder).
)

echo.
echo Done! You can now play the .mp4 files in this folder.
pause
