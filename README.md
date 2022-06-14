# OCR Image Cataloguer
This script goes through all files in a given directory and runs tesseract (google's locally run OCR tool) on them, storing the file's name and text in an sqlite3  database. Simple search queries can then be run on the DB within the script's CLI.

Python dependencies:  ```sqlite3, os, pytesseract, PIL, sys```
System dependencies: you'll need to have tesseract and sqlite3 installed. I've only run the script on linux.

Flags cant be stacked, only use one at a time. Options:
- **-h**: Print flag details and examples of use
- **-n**: Erase any existing database with the specified name and create a new one
- **-u**: Update the database, appends the results of new images and prunes entries from the DB that are no longer found in the directory
- **-q**: Query the database, returns the filenames for any case insensitive match
  - **-qd**: Same as **-q**, but allows the user to specify a delimiter different from newline, such as space, allowing the result to be piped into an image viewer
  - **-qh**: Creates a hardlink of all matching files on the specified folder

Run the script with
`python handler.py <flag> <path_of_db> <target_folder/search_string>`