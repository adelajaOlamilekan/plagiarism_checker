import os
import sys
import re
from io import StringIO
import tokenize
import keyword
import hashlib
import chardet
import fitz
from docx import Document
import json
from tqdm import tqdm
from collections import deque


SINGLE_LINE_COMMENT_PATTERN = r'#.*'
DOC_STRING_PATTERN = r'(""".*?"""|\'\'\'.*?\'\'\')'
REPLACEMENT_FOR_IDENTIFIERS = 'var'
REPLACEMENT_FOR_NUMBERS = 'num'
LINES_OF_CODE = 1000
TEST_SCRIPT_NAME1 = 'gpt_test1.py'
TEST_SCRIPT_NAME2 = 'gpt_test2.py'
K_GRAM = 5
WINDOW_SIZE = 4
PERCENTAGE = 100
HEXADECIMAL = 16
DOCUMENT_EXTENSION = ['.doc', '.docx']
PDF_EXTENSION = '.pdf'
DOCUMENT_EXTENSIONS = ['.doc', '.docx', '.pdf']


# def generate_test_script():
#     lines = []
#     for i in range(LINES_OF_CODE):
#         lines.extend(
#             (
#                 f"def function_{i}(x, y):",
#                 f"    '''Function {i} docstring''' ",
#                 "    result = x + y",
#                 "    for j in range(10):",
#                 "        if j % 2 == 0:",
#                 "            result += j",
#                 "        else:",
#                 "            result -= j",
#                 f"    return result\n",
#             )
#         )
#     lines = '\n'.join(lines)

#     with open(TEST_SCRIPT_NAME1, 'w') as file:
#         file.write(lines)

def read_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf_document:
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
    return text

def read_doc(file_path):
    document = Document(file_path)
    return "".join(paragraph.text for paragraph in document.paragraphs)

def read_file(file_path, extension=None):
    if extension == PDF_EXTENSION:
        return read_pdf(file_path)
    elif extension in DOCUMENT_EXTENSION:
        return read_doc(file_path)
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def preprocessor(code, extension=None):
    if extension == PDF_EXTENSION or extension in DOCUMENT_EXTENSION:
        code = code.lower()
        return code
    
    #Convert to lowercase
    code = code.lower()

    #Remove comments from code
    code = re.sub(SINGLE_LINE_COMMENT_PATTERN, '', code)

    #Remove docstrings from code
    code = re.sub(DOC_STRING_PATTERN, '', code, flags=re.DOTALL)
 
    #Remove whitespace from code
    code = re.sub(r'\s+', ' ', code).strip()

    return code

def tokenize_code(code):
    #Tokenize code
    code = StringIO(code).readline
    code_stream = tokenize.generate_tokens(code)


    #Normalize code
    normalized_tokens = []

    try:
        for token in code_stream:

            #Normalize identifiers(variable and function names except keywords)
            if token.type == tokenize.NAME and not keyword.iskeyword(token.string):
                normalized_tokens.append(REPLACEMENT_FOR_IDENTIFIERS)
            
            #Normalize numbers
            elif token.type == tokenize.NUMBER:
                normalized_tokens.append(REPLACEMENT_FOR_NUMBERS)

            else:
                normalized_tokens.append(token.string)
    except tokenize.TokenError as e:
        raise e

    return ' '.join(normalized_tokens)

def create_k_gram(normalized_code, k_gram):
    return  [normalized_code[i:i+k_gram] for i in range(len(normalized_code)-k_gram+1)]

def create_hash_table(k_gram_list):
    #Create hashes for the k-gram tokens
    return [int(hashlib.sha256(k_gram.encode('utf-8')).hexdigest(), HEXADECIMAL) for k_gram in k_gram_list]


def winnow(hashes, window_size):
    fingerprints = []
    deque_window = deque()

    try:
        hashes[window_size]

    except IndexError as e:
        print(f'{e}: Window size is greater than the number of hashes')

    # Process the first window
    for i in range(window_size):
        while deque_window and hashes[i] <= hashes[deque_window[-1]]:
            deque_window.pop()
        deque_window.append(i)

    # Process the rest of the windows
    for i in range(window_size, len(hashes)):
        # Append the minimum of the previous window
        fingerprints.append((hashes[deque_window[0]], deque_window[0]))

        # Remove elements not within the sliding window
        while deque_window and deque_window[0] <= i - window_size:
            deque_window.popleft()

        # Add the current element
        while deque_window and hashes[i] <= hashes[deque_window[-1]]:
            deque_window.pop()
        deque_window.append(i)

    # Append the minimum of the last window
    fingerprints.append((hashes[deque_window[0]], deque_window[0]))

    return fingerprints

# def winnow(hashes, window_size):
#     fingerprints = []

#     try:
#         hashes[window_size]

#     except IndexError as e:
#         print(f'{e}: Window size is greater than the number of hashes')

#     right_index = window_size

#     for left_index in range(len(hashes)-window_size+1):
#         min_value = hashes[left_index]
#         min_index = left_index
#         for sub_index in range(min_index, right_index):
#             if hashes[sub_index] <= min_value and sub_index > min_index:
#                 min_value = hashes[sub_index]
#                 min_index = sub_index

#         #if the fingerprint is not in the fingerprints list, add it
#         if (min_value, min_index) not in fingerprints:      
#             fingerprints.append((min_value, min_index))

#         right_index += 1

#     return fingerprints

def compare_fingerprints(fingerprints1, fingerprints2):
    hashes1 = {hash_value for hash_value, _ in fingerprints1}
    hashes2 = {hash_value for hash_value, _ in fingerprints2}
    common_hashes = hashes1.intersection(hashes2)

    return len(common_hashes)/max(len(hashes1), len(hashes2)) * PERCENTAGE


def check_plagiarism(files=None, k_gram=None):

    #Checking if all files are in .doc, .docx or .pdf format
    # for file in tqdm(files, desc="Validating document extensions..."):
    #     file_extension = os.path.splitext(file)[1]
    #     if file_extension not in DOCUMENT_EXTENSIONS:
    #         print(file_extension)
    #         raise ValueError('Files must be in  .doc, .docx or .pdf format')
    
    #Create a dictionary of filename and fingerprint
    fingerprint_dict = {}
    for file in tqdm(files, desc="Fingerprinting files..."):
        file_extension = os.path.splitext(file)[1]
        normalized_code = preprocessor(read_file(file, file_extension), file_extension)
        k_gram_list = create_k_gram(normalized_code, k_gram)
        fingerprint = winnow(create_hash_table(k_gram_list), WINDOW_SIZE)
        fingerprint_dict[file] = fingerprint
    
    #Compare the fingerprints of the files
    similarity_scores = {}

    file_names = list(fingerprint_dict.keys())

    for i in tqdm(range(len(file_names)), desc="Comparing fingerprints..."):
        for j in range(i + 1, len(file_names)):
            similarity = compare_fingerprints(fingerprint_dict[file_names[i]], fingerprint_dict[file_names[j]])
            similarity_scores[f"{file_names[i]} vs {file_names[j]}"] = similarity
    
    return similarity_scores


if __name__ == '__main__':

    # generate_test_script()

    if len(sys.argv) == 3:
        filename1= sys.argv[1]
        filename2= sys.argv[2]
        check_plagiarism(filename1=filename1, filename2=filename2, k_gram=K_GRAM)
    else:
        print('Usage: python main.py <filename1> <filename2>')

