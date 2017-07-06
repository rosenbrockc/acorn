"""Lauches the acorn ui server and opens the browser to the correct page.
"""
import webbrowser
import os
from multiprocessing import Process
import time

def open_window():
    """Opens a new tab for the acorn notebook to be displayed in.
    """
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:8000/',new=2,autoraise=True)
    
def launch_server():
    """Launches the django server at 127.0.0.1:8000
    """
    print(os.path.dirname(os.path.abspath(__file__)))
    cur_dir = os.getcwd()
    path = os.path.dirname(os.path.abspath(__file__))
    run = True
    os.chdir(path)
    os.system('python manage.py runserver --nostatic')
    os.chdir(cur_dir)

if __name__ == '__main__':
    Process(target=launch_server).start()    
    Process(target=open_window).start()
