open cmd

cd to your project dir 

python -m venv venv

venv\Scripts\activate 

pip install -r requirements.txt

change your keyauth and replace the dll download url in main_window.py 

Run: python main.py

To convert it to exe use 

pyinstaller version 6.20.0 

Python 3.11.0  

pyinstaller -F -w --uac-admin -i icon.ico main.py
