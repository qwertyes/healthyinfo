@echo off
cd /d "D:\AI\HealthyInfo\video-pipeline"
if not exist logs mkdir logs
"C:\Users\qwert\AppData\Local\Programs\Python\Python313\python.exe" -u daily_auto_run.py >> logs\daily_run.log 2>&1
