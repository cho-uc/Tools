'''
Python script to upload maven repository to Nexus
'''
import requests
from requests.auth import HTTPBasicAuth
import pathlib

'''
# curl -v --netrc --upload-file path/to/local/file.txt http://nexus.opscloud.myurl.com/repository/myProject/myPackage/

'''
\
base_url = "http://nexus.opscloud.myurl.com/repository/myProject/myPackage/"
remote_dir = 'v1.2.3/'

source_dir = pathlib.Path("/path/to/local/maven/repository/").rglob("*")

myFiles = [] # full path of the files
myFilesRelativePath = [] # relative path start with org/, int/, com/, edu/, de/, etc

# Separate between files and dir
for item in source_dir:
    if item.is_file():
        myFiles.append(str(item))
        # Get relative path by shortening the full path
        short_path = str(item)[92:]    # this should be modified if source_dir is changed
        myFilesRelativePath.append(short_path)

print("List of files: ")
for idx, item in enumerate(myFilesRelativePath):
    print("\t", (idx + 1), item)

assert(len(myFiles) == len(myFilesRelativePath))
print("Remote dir: "+ remote_dir)

user_approval = input('File paths should start with org/, int/, com/, edu/, de/, etc. Continue (y/n)?\n')

print("\n")
# Credential will automatically taken from .netrc file stored in the machine
# Can be changed to hard-coded user/password 
if user_approval.lower() == 'y':
    for idx, item in enumerate(myFilesRelativePath):
        print("Uploading ... ", (idx + 1), item)
        with open(myFiles[idx], 'rb') as f:   # use full path for opening file
            res = requests.put(base_url + remote_dir + item, data=f) # use netrc for authentication
            print(res) # should output HTTP Response [201]


print("End of script")
