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

    return file_text

def create_k_gram(file_text, k_gram):
    k_gram_list = []
    for i in range(len(file_text) - k_gram + 1):
        k_gram_list.append(file_text[i:i+k_gram])
    
    return k_gram_list
 
def main(filename=None, k_gram=None):
    file_text = read_file(filename)
    file_text = preprocessor(file_text)
    k_gram_list = create_k_gram(file_text, int(k_gram))

if __name__ == '__main__':

    if len(sys.argv) == 3:
        filename = sys.argv[1]
        k_gram = sys.argv[2]
        main(filename=filename, k_gram=k_gram)
    else:
        print('Usage: python main.py <filename> <k-gram>')
