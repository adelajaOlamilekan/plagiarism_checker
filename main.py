import os
import sys
import json

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()
    
def preprocessor(file_text):
    #Convert to lowercase
    file_text = file_text.lower()

    #Remove characters that are in the config file
    with open('config.json', 'r') as file:
        config = json.loads(file.read())

        for category in config['special_characters'].values():
            for char in category:
                if char in file_text:
                    print(char)
                    file_text = file_text.replace(char, '')
    print(file_text)
 
def main(filename=None):
    file_text = read_file(filename)
    preprocessor(file_text)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        main(filename)
    else:
        print('Usage: python main.py <filename>')
