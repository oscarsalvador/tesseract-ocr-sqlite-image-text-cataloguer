import sqlite3
import os
import pytesseract
from PIL import Image
import sys

def manual():
    print('''Usage: python handler.py <flag> <flag-args>
Both absolute and relative paths will work, as well as any combination.

    -n      New database: Erase any existing db with the same name and scan all files from scratch
                python handler.py -n ./relative-path/example-name.db ./relative-path/example-folder/
                python handler.py -n /absolute-path/example-name.db /absolute-path/example-folder

    -u      Update database: Scan any files missing from the db, and add their contents
                python handler.py -u ./relative-path/example-name.db ./relative-path/example-folder/
                python handler.py -u /absolute-path/example-name.db /absolute-path/example-folder

    -q      Query database: Returns the filenames for any case insensitive match within the db to the specified string.
            Results will be separated by newline.
                python handler.py -q ./relative-path/example-name.db "string to search"
                python handler.py -q /absolute-path/example-name.db "string to search"

    -qd     Query with specific Delimiter: same as -q, but allows the user to specify a different way to separate results. 
            Any string will be used, but this allows for the use of spaces, to feed the results into other programs
                python handler.py -qd ./relative-path/example-name.db "string to search" " "
                python handler.py -qd /absolute-path/example-name.db "string to search" " "

    -qh     Query with Hardlinks: a hardlink of all matching files will be created whichever folder the user specifies
                python handler.py -qh ./relative-path/example-name.db "string to search" /relative-path/placement-folder/
                python handler.py -qh /absolute-path/example-name.db "string to search" " " /absolute-path/placement-folder
            
    ''')
    exit()


def addEntry(connexion, imgPath):
    if(not os.path.isfile(imgPath)):
        print("Skipped  " + imgPath + " for being a dir")
        return

    try:
        img = Image.open(imgPath)
    except:
        print("Skipped  " + imgPath + " for not being a valid image")
        return

    pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
    text = pytesseract.image_to_string(img, lang='eng')

    print("Scanning " + imgPath)
    connexion.execute('''
        INSERT INTO img_contents (filename, contents) VALUES (?,?)
        ''',
        # (imgPath.split("/")[-1], text)
        (imgPath, text)
    )
    connexion.commit()


def newDB(dbPath, dirPath):
    if os.path.exists(dbPath):
        os.remove(dbPath)

    connexion = sqlite3.connect(dbPath)
    connexion.execute('''
        CREATE TABLE "img_contents" (
            "filename"	TEXT,
            "contents"	TEXT
        );
    ''')

    for filename in os.listdir(dirPath):
        imgPath = dirPath + "/" + filename
        addEntry(connexion, imgPath)

    connexion.close()


def updateDB(dbPath, dirPath):
    if not os.path.exists(dbPath):
        print("No " + dbPath + " DB found")
        return

    connexion = sqlite3.connect(dbPath)
    cursor = connexion.cursor()
    cursor.execute('''
        SELECT filename FROM img_contents;
    ''')
    storedFiles = cursor.fetchall()

    #add any new files
    for filename in os.listdir(dirPath):
        filefound = False
        
        for storedName in storedFiles:
            if storedName[0].__contains__(filename): #returns array with tuples of 1 element
                print("Skipped  " + dirPath + "/" + filename + " since it's already in db")
                filefound = True
                storedFiles.remove(storedName)
                break
    
        if(not filefound):
            print("Adding   " + dirPath + "/" + filename + " since it wasn't already in db")
            imgPath = dirPath + "/" + filename
            addEntry(connexion, imgPath)
        
    #files that were no longer found in the dir
    purge_pending = ""
    for remaining in storedFiles:
        remaining = str(remaining).replace("(", "").replace(")", "")
        print("Purging " + remaining + " since it's no longer in the dir")
        purge_pending += remaining
    purge_pending = purge_pending.replace("(", "").replace(")", "")
    
    connexion.execute('''
        DELETE FROM img_contents WHERE filename IN (%s)
    ''' % purge_pending[:-1] #last pos contains a comma
    )
    connexion.commit()
    connexion.close()
    

def queryDB(dbPath, query):
    connexion = sqlite3.connect(dbPath)
    cursor = connexion.cursor()
    cursor.execute('''
        SELECT filename FROM img_contents WHERE contents LIKE '%s';
        ''' 
        % ("%" + query + "%") #case insensitive but otherwise
    )

    foundFiles = cursor.fetchall()
    connexion.close()

    return foundFiles
    

def printResults(dbPath, query, delimiter):
    foundFiles = queryDB(dbPath, query)
    for filename in foundFiles:
        print(filename[0], end=delimiter)
    print()


def hardlinkResults(results, placementDirPath): #hardlinks en /tmp/ para visualizar
    if not os.path.exists(placementDirPath):
        os.mkdir(placementDirPath)

    for filename in results:
        # command = "ln " + filename[0] + " /tmp/OCR-handler/" + filename[0].split("/")[-1]
        command = "ln " + filename[0] + " " + placementDirPath + "/" + filename[0].split("/")[-1]
        os.system(command) 
    print("Hardlinked query result files in " + placementDirPath)


def main():    
    if len(sys.argv) < 2:
        manual()

    if sys.argv[1] == "-h" or sys.argv[1] == "--help":
        manual()
    if sys.argv[1] == "-n" and sys.argv.__len__() == 4:
        if not os.path.exists(sys.argv[3]):
            manual()
        newDB(os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]))
        exit()
    if sys.argv[1] == "-u" and sys.argv.__len__() == 4:
        if not (os.path.exists(sys.argv[2] or os.path.exists(sys.argv[3]))):
            manual()
        updateDB(os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]))
        exit()
    if sys.argv[1] == "-q" and sys.argv.__len__() == 4:
        if not os.path.exists(sys.argv[2]):
            manual()
        printResults(os.path.abspath(sys.argv[2]), sys.argv[3], "\n")
        exit()
    if sys.argv[1] == "-qd" and sys.argv.__len__() == 5:
        if not os.path.exists(sys.argv[2]):
            manual()
        printResults(os.path.abspath(sys.argv[2]), sys.argv[3], sys.argv[4])
        exit()
    if sys.argv[1] == "-qh" and sys.argv.__len__() == 5:
        if not (os.path.exists(sys.argv[2] or os.path.exists(sys.argv[4]))):
            manual()
        hardlinkResults(queryDB(os.path.abspath(sys.argv[2]), sys.argv[3]), os.path.abspath(sys.argv[4]))
        exit()

    manual()


if __name__ == '__main__':
    main()