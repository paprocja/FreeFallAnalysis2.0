# handles passing the dated csv folder inbetween python files to follow correct file path
date_folder = ""

def get_date_folder():
    return date_folder

def set_date_folder(date):
    global date_folder
    date_folder = date