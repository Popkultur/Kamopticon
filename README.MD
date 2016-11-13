Kamopticon IP-Kamera-Betrachter



Darstellung von unbegrenzt vielen (so viel die Leitung hergibt) IP-Kameras, Möglichkeit der Aufnahme von Einzel-, Reihenbildern und Videos. Massenprüfung auf Verfügbarkeit und Verschlagwortung aller Kameras. Einordnung in zwei Kategorien (Sichtbar und Versteckte).



Installation mit Python 3.5 oder höher.

Anleitung für virtuelle Laufzeitumgebung unter Windows:

\Path\to\Source> C:\Users\Username\AppData\Local\Programs\Python\Python35\Tools\scripts\pyvenv.py \Path\to\Source\venv

> <venv>\Scripts\activate.bat

(venv)> pip install eventlet
(venv)> pip install flask
(venv)> pip install requests
(venv)> pip install numpy
(venv)> pip install flask_socketio
(venv)> pip install python-slugify

Installieren Sie openCV 3.1.0 oder höher ( http://www.lfd.uci.edu/~gohlke/pythonlibs/#opencv )
(venv)> pip install opencv_python-3.1.0-cp35-cp35m-win_amd64.whl

Setzen Sie die Umgebungsvariable OPENCV_FFMPEG_DLL_DIR auf den Pfad zu den openCV DLLs (üblicherweise unter (...)\venv\Lib\site-packages)

Installieren Sie ggfs. das C++ Visual Redistributable 2015

Um das Programm auszuführen, rufen sie
> main.py
auf.

Navigieren Sie im Browser zu http://127.0.0.1 (localhost)

Importieren Sie eine Liste von Kameras aus einer Text-Datei.

Beachten Sie die Lizenz unter LICENSE.TXT