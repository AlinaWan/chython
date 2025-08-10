# -*- coding: utf-8 -*-
import re
import sys
import codecs

# This dictionary defines the mapping from Chinese words to Python keywords.
# It is used here to derive the inverse mapping.
original_ch_py_keywords = {
    # Logic operators and boolean values
    u'和': "and", u"且": "and", u"或": "or", u"或者": "or",
    u"真": "True", u"假": "False", u"实": "True", u"虛": "False", u"空": "None",
    # Comparison operators
    u"等于": "==", u"少于": "<", u"多于": ">", u"少于或等于": "<=", u"少于或者等于": "<=",
    u"多于或等于": ">=", u"多于或者等于": ">=", u"不等于": "!=",
    # Definition keywords
    u'定义': "def", u"类": "class", u"我": "self", u"自个儿": "self", u"共用": "global",
    u"全域": "global",
    # Import statements
    u"从": "from", u"导入": "import", u"作为": "as",
    # Flow control
    u"返回": "return", u"略过": "pass", u"引发": "raise", u"继续": "continue",
    # Conditional statements
    u"如果": "if", u"假使": "elif", u"否则如果": "elif", u"否则": "else",
    # Loop statements
    u"取": "for", u"自": "in", u"在": "in", u"不在": "not in",
    u"当": "while", u"跳出": "break", u"中断": "break",
    # Exception handling
    u"尝试": "try", u"异常": "except", u"最后": "finally", u"申明": "assert",
    # Built-in functions and keywords
    u"执行": "exec", u"函数": "lambda", u"打印": "print", u"伴隨": "with",
    u"产生": "yield",
    # Type casting functions
    u"整数": "int", u"字符串": "str",
    # Common functions and modules
    u"范围": "range",
    u"系统": "sys", u"数学": "math",
}

# Create the inverse mapping: Python keyword -> Preferred Chinese keyword.
# Since multiple Chinese words can map to the same Python keyword (e.g., '和' and '且' both map to 'and'),
# we explicitly choose one preferred Chinese word for each Python keyword to ensure deterministic translation.
inverse_keywords = {
    "and": u"和",
    "or": u"或",
    "True": u"真",
    "False": u"假",
    "None": u"空",
    "==": u"等于",
    "<": u"少于",
    ">": u"多于",
    "<=": u"少于或等于",
    ">=": u"多于或等于",
    "!=": u"不等于",
    "def": u"定义",
    "class": u"类",
    "self": u"我",
    "global": u"共用",
    "from": u"从",
    "import": u"导入",
    "as": u"作为",
    "return": u"返回",
    "pass": u"略过",
    "raise": u"引发",
    "continue": u"继续",
    "if": u"如果",
    "elif": u"假使", # Preferred over '否则如果'
    "else": u"否则",
    "for": u"取",
    "in": u"在",     # Preferred over '自'
    "not in": u"不在",
    "while": u"当",
    "break": u"跳出", # Preferred over '中断'
    "try": u"尝试",
    "except": u"异常",
    "finally": u"最后",
    "assert": u"申明",
    "exec": u"执行",
    "lambda": u"函数",
    "print": u"打印",
    "with": u"伴隨",
    "yield": u"产生",
    "int": u"整数",
    "str": u"字符串",
    "range": u"范围",
    "sys": u"系统",
    "math": u"数学",
}

# These are characters that act as delimiters for words in the code.
# They help in tokenizing the input lines.
splitters = [
    '.', ',', '{', '}', '(', ')', '[', ']', '+', '-', '/', '*', '\t', '"', '\'', '\n', ' '
]

def from_unicode_name(word):
    """
    Converts a string encoded as 'n<ordinal>n<ordinal>...' back to Chinese characters.
    This function reverses the encoding logic found in the original 'to_unicode_name' function.
    
    For example: 'n20320n22909' will be decoded back to '你好'.
    It is designed to handle cases where other characters might be mixed with the encoding.
    """
    decoded_parts = []
    last_idx = 0
    match_found_and_decoded = False

    # Find all occurrences of the 'n' followed by digits pattern
    for match in re.finditer(r'n(\d+)', word):
        # Add any non-encoded text that appears before the current match
        if match.start() > last_idx:
            decoded_parts.append(word[last_idx:match.start()])

        try:
            # Convert the numeric part of the match to an integer and then to a character
            ordinal = int(match.group(1))
            decoded_parts.append(chr(ordinal))
            match_found_and_decoded = True
        except ValueError:
            # If the numeric part is not a valid integer, treat the entire 'n<digits>' sequence as literal text
            decoded_parts.append(match.group(0))
        
        last_idx = match.end()
    
    # Add any remaining non-encoded text after the last match
    if last_idx < len(word):
        decoded_parts.append(word[last_idx:])

    # If no 'n<digits>' pattern was found and successfully decoded, return the original word.
    # This prevents misinterpretation of legitimate variable names that might start with 'n'
    # but are not intended to be unicode-encoded.
    if not match_found_and_decoded and not decoded_parts:
        return word
    
    return "".join(decoded_parts)

def tokenize_line(line_str):
    """
    Splits a single line of code into a list of meaningful tokens.
    Tokens include Python keywords, variable names, literals, operators, and splitters
    (like punctuation, whitespace, and newlines).
    This function ensures that even splitters at the end of the line or consecutive
    splitters are handled correctly.
    """
    tokens = []
    current_index = 0
    line_length = len(line_str)

    while current_index < line_length:
        next_splitter_position = -1

        # Search for the next splitter character from the current position
        for i in range(current_index, line_length):
            if line_str[i] in splitters:
                next_splitter_position = i
                break
        
        if next_splitter_position == -1:
            # If no splitter is found until the end of the line,
            # the rest of the line is considered a single word/token.
            word = line_str[current_index:]
            if word: # Add the word part only if it's not empty
                tokens.append(word)
            current_index = line_length # Move index to end to terminate the loop
        else:
            # If a splitter is found:
            # 1. Extract the word part before the splitter.
            word = line_str[current_index:next_splitter_position]
            if word: # Add the word part only if it's not empty
                tokens.append(word)
            
            # 2. Add the splitter character itself as a token.
            tokens.append(line_str[next_splitter_position])
            
            # 3. Move the current_index past the splitter.
            current_index = next_splitter_position + 1
            
    return tokens

def translate_to_chpython(token_list, inv_keywords_map):
    """
    Translates a list of Python tokens into their ChPython (Chinese Python) equivalents.
    This process involves two main steps:
    1. Mapping standard Python keywords (like 'if', 'for', 'def') to their Chinese counterparts.
    2. Decoding any variable names that were previously encoded into the 'n<ordinal>' format
       back into their original Chinese characters.
    Tokens that are neither keywords nor encoded names remain unchanged.
    """
    translated_tokens = []
    for token in token_list:
        # First, attempt to decode the token as a unicode-encoded variable name.
        # This takes precedence because a token might be 'n12345' which is a variable name,
        # not a Python keyword.
        decoded_name = from_unicode_name(token)
        if decoded_name != token:
            # If from_unicode_name successfully decoded it (meaning it was an encoded name),
            # use the decoded Chinese version.
            translated_tokens.append(decoded_name)
        # Otherwise, if it's not an encoded name, check if it's a standard Python keyword
        # that needs to be translated into Chinese.
        elif token in inv_keywords_map:
            translated_tokens.append(inv_keywords_map[token])
        else:
            # If the token is neither an encoded name nor a recognized Python keyword,
            # it is kept as is (e.g., regular variable names, literals, operators not in keywords).
            translated_tokens.append(token)
    return translated_tokens

# Main execution block
if __name__ == "__main__":
    # Check if the correct number of command-line arguments are provided.
    if len(sys.argv) != 3:
        print("Usage: python python_to_chpython.py <source_python_file> <target_chpython_file>")
        sys.exit(1)

    source_file_path = sys.argv[1]
    target_file_path = sys.argv[2]

    try:
        # Open the source Python file for reading. We assume it's UTF-8 encoded.
        with codecs.open(source_file_path, encoding='utf-8', mode='r') as source_f:
            # Open the target ChPython file for writing. It needs to be UTF-8 encoded
            # to correctly store Chinese characters.
            with codecs.open(target_file_path, encoding='utf-8', mode='w') as target_f:
                # Read the source file line by line until the end.
                line = source_f.readline()
                while line != '':
                    # Tokenize the current line into a list of words and splitters.
                    original_tokens = tokenize_line(line)
                    # Translate the tokenized list from Python to ChPython.
                    translated_tokens = translate_to_chpython(original_tokens, inverse_keywords)
                    # Join the translated tokens back into a string and write to the target file.
                    # We use "".join() because 'tokenize_line' separates words and splitters,
                    # and we want to preserve the original spacing/structure as much as possible.
                    target_f.write("".join(translated_tokens))
                    line = source_f.readline()
        print(f"Successfully translated '{source_file_path}' to '{target_file_path}'.")

    except FileNotFoundError:
        print(f"Error: One of the specified files was not found. Please check the provided file paths.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
