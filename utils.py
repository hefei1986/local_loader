import commands
import os

def get_file_list(path):
    str_command = "ls -t "+path + " | grep png"
    ret, data = commands.getstatusoutput(str_command)
    if ret != 0:
        return None
    else:
        ret_array = data.split("\n")
        return ret_array

def file_get_content(path):
    if not path:
        return None
    
    if not os.path.exists(path):
        return None 

    content = ''
    for line in open(path):
        content += line
    
    return content
