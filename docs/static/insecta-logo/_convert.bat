@echo off
set PATH=\Bin\cygwin64\bin;%PATH%
set PATH=\Bin\ImageMagick;%PATH%
set PATH=\Bin\imagetools;%PATH%
set PATH=\Bin\7-Zip;%PATH%
set PATH=\Bin\ghostscript\bin;%PATH%
set PATH=\Bin\xpdf;%PATH%
set PATH=\Bin\Python39;%PATH%

set convert=convert.exe -density 300 -colorspace Gray +dither -colors 256

%convert% arachnida.pdf   ../icon-arachnida.png
%convert% coleoptera.pdf  ../icon-coleoptera.png
%convert% diptera.pdf     ../icon-diptera.png
%convert% hemiptera.pdf   ../icon-hemiptera.png
%convert% hymenoptera.pdf ../icon-hymenoptera.png
%convert% insecta.pdf     ../icon-insecta.png
%convert% lepidoptera.pdf ../icon-lepidoptera.png
%convert% orthoptera.pdf  ../icon-orthoptera.png
pause