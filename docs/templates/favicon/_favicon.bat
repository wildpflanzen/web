set convert=/Bin/imagemagick/convert.exe 
for %%f in (*.png) do %convert%  %%f -resize 32x32  %%f.ico
pause