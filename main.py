import os
import sys
import re
from io import StringIO
import tokenize
import keyword
import hashlib

SINGLE_LINE_COMMENT_PATTERN = r'#.*'
DOC_STRING_PATTERN = r'(""".*?"""|\'\'\'.*?\'\'\')'
REPLACEMENT_FOR_IDENTIFIERS = 'var'
REPLACEMENT_FOR_NUMBERS = 'num'
LINES_OF_CODE = 1000
TEST_SCRIPT_NAME1 = 'test_script.py'
TEST_SCRIPT_NAME2 = 'test_script1.py'
K_GRAM = 5
WINDOW_SIZE = 4
PERCENTAGE = 100
HEXADECIMAL = 16


def generate_test_script():
    lines = []
    for i in range(LINES_OF_CODE):
        lines.extend(
            (
                f"def function_{i}(x, y):",
                f"    '''Function {i} docstring'''",
                "    result = x + y",
                "    for j in range(10):",
                "        if j % 2 == 0:",
                "            result += j",
                "        else:",
                "            result -= j",
                f"    return result\n",
            )
        )
    lines = '\n'.join(lines)

    with open(TEST_SCRIPT_NAME1, 'w') as file:
        file.write(lines)

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()
    
def preprocessor(code):
    #Convert to lowercase
    code = code.lower()

    #Remove comments from code
    code = re.sub(SINGLE_LINE_COMMENT_PATTERN, '', code)

    #Remove docstrings from code
    code = re.sub(DOC_STRING_PATTERN, '', code, flags=re.DOTALL)
    # print(code)
 
    #Remove whitespace from code
    code = re.sub(r'\s+', ' ', code).strip()
    # print(code)

    #Tokenize code
    code = StringIO(code).readline
    code_stream = tokenize.generate_tokens(code)


    #Normalize code
    normalized_tokens = []

    for token in code_stream:

        #Normalize identifiers(variable and function names except keywords)
        if token.type == tokenize.NAME and not keyword.iskeyword(token.string):
            normalized_tokens.append(REPLACEMENT_FOR_IDENTIFIERS)
        
        #Normalize numbers
        elif token.type == tokenize.NUMBER:
            normalized_tokens.append(REPLACEMENT_FOR_NUMBERS)

        else:
            normalized_tokens.append(token.string)

    return ' '.join(normalized_tokens)

def create_k_gram(normalized_code, k_gram):
    return  [normalized_code[i:i+k_gram] for i in range(len(normalized_code)-k_gram+1)]

def create_hash_table(k_gram_list):
    #Create hashes for the k-gram tokens
    return [int(hashlib.sha256(k_gram.encode('utf-8')).hexdigest(), HEXADECIMAL) for k_gram in k_gram_list]

def winnow(hashes, window_size):
    fingerprints = []

    try:
        hashes[window_size]

    except IndexError as e:
        print(f'{e}: Window size is greater than the number of hashes')

    right_index = window_size

    for left_index in range(len(hashes)-window_size+1):
        min_value = hashes[left_index]
        min_index = left_index
        for sub_index in range(min_index, right_index):
            if hashes[sub_index] <= min_value and sub_index > min_index:
                min_value = hashes[sub_index]
                min_index = sub_index
        fingerprints.append((min_value, min_index))
        right_index += 1

    print(list(set(fingerprints)))
    return fingerprints

def compare_fingerprints(fingerprints1, fingerprints2):
    hashes1 = {hash_value for hash_value, _ in fingerprints1}
    hashes2 = {hash_value for hash_value, _ in fingerprints2}
    common_hashes = hashes1.intersection(hashes2)

    return len(common_hashes)/max(len(hashes1), len(hashes2)) * PERCENTAGE


def main(filename1=None, filename2=None, k_gram=None):
    normalized_code1 = preprocessor(read_file(filename1))
    normalized_code2 = preprocessor(read_file(filename2))
    k_gram_list1 = create_k_gram(normalized_code1, K_GRAM)
    k_gram_list2 = create_k_gram(normalized_code2, K_GRAM)
    fingerprint1 = winnow(create_hash_table(k_gram_list1), WINDOW_SIZE)
    fingerprint2 = winnow(create_hash_table(k_gram_list2), WINDOW_SIZE)
    similarity = compare_fingerprints(fingerprint1, fingerprint2)
    print(f'Similarity between {filename1} and {filename2} is {similarity}%')

if __name__ == '__main__':

    # generate_test_script()

    if len(sys.argv) == 3:
        filename = sys.argv[1]
        k_gram = sys.argv[2]
        main(filename1=TEST_SCRIPT_NAME1, filename2=TEST_SCRIPT_NAME2, k_gram=K_GRAM)
    else:
        print('Usage: python main.py <filename> <k-gram>')

