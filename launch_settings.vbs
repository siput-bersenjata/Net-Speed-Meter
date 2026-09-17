Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\bram\Documents\Coding\Speed meter"
WshShell.Run "pythonw.exe main.py --settings", 0, False
