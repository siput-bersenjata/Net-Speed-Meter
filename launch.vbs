Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\bram\Documents\Coding\Speed meter"
WshShell.Run "pythonw.exe main.py", 0, False
