@echo off
cd /d "%~dp0"
echo ============================================================
echo  Un Jour a Giverny - Lossless MP4 Reassembly (Windows)
echo ============================================================
echo.

if exist "monet_un_jour_a_giverny_720p.mp4.part.00" (
  echo [1/2] Merging 720p MP4 ^(5 chunks^)...
  copy /b "monet_un_jour_a_giverny_720p.mp4.part.00"+"monet_un_jour_a_giverny_720p.mp4.part.01"+"monet_un_jour_a_giverny_720p.mp4.part.02"+"monet_un_jour_a_giverny_720p.mp4.part.03"+"monet_un_jour_a_giverny_720p.mp4.part.04" "monet_un_jour_a_giverny_720p.mp4" >nul
  if exist "monet_un_jour_a_giverny_720p.mp4" (
    echo       OK: monet_un_jour_a_giverny_720p.mp4 ready!
  ) else (
    echo       FAILED: 720p merge failed.
  )
) else (
  echo [1/2] Skipped 720p ^(chunks not found in this folder^).
)

echo.

if exist "monet_un_jour_a_giverny_1080p.mp4.part.00" (
  echo [2/2] Merging 1080p MP4 ^(13 chunks^)...
  copy /b "monet_un_jour_a_giverny_1080p.mp4.part.00"+"monet_un_jour_a_giverny_1080p.mp4.part.01"+"monet_un_jour_a_giverny_1080p.mp4.part.02"+"monet_un_jour_a_giverny_1080p.mp4.part.03"+"monet_un_jour_a_giverny_1080p.mp4.part.04"+"monet_un_jour_a_giverny_1080p.mp4.part.05"+"monet_un_jour_a_giverny_1080p.mp4.part.06"+"monet_un_jour_a_giverny_1080p.mp4.part.07"+"monet_un_jour_a_giverny_1080p.mp4.part.08"+"monet_un_jour_a_giverny_1080p.mp4.part.09"+"monet_un_jour_a_giverny_1080p.mp4.part.10"+"monet_un_jour_a_giverny_1080p.mp4.part.11"+"monet_un_jour_a_giverny_1080p.mp4.part.12" "monet_un_jour_a_giverny_1080p.mp4" >nul
  if exist "monet_un_jour_a_giverny_1080p.mp4" (
    echo       OK: monet_un_jour_a_giverny_1080p.mp4 ready!
  ) else (
    echo       FAILED: 1080p merge failed.
  )
) else (
  echo [2/2] Skipped 1080p ^(chunks not found in this folder^).
)

echo.
echo All done! You can now play the .mp4 files in this folder.
pause
