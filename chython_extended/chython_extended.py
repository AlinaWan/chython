# -*- coding: utf-8 -*-
import re
import sys
import codecs
import os
import ast # Import the AST library

class Transpiler:
    """
    A class for two-way transpilation between English Python and Chinese Python.
    Uses AST for robust code structure preservation for identifiers.
    Keyword translation is handled in pre/post AST passes.
    """
    def __init__(self):
        # English to Chinese keywords (for English -> Chinese transpilation)
        self.en_to_zh_keywords = {
            "and": u'和', "or": u'或', "True": u'真', "False": u'假', "None": u'空',
            "==": u'等于', "<": u'少于', ">": u'多于', "<=": u'少于或等于', ">=": u'多于或等于', "!=": u'不等于',
            "def": u'定义', "class": u'类', "self": u'我', "global": u'共用',
            "from": u'从', "import": u'导入', "as": u'作为',
            "return": u'返回', "pass": u'略过', "raise": u'引发', "continue": u'继续',
            "if": u'如果', "elif": u'假使', "else": u'否则',
            "for": u'取', "in": u'自', "not in": u'不在',
            "while": u'当', "break": u'跳出',
            "try": u'尝试', "except": u'异常', "finally": u'最后', "assert": u'申明',
            "exec": u'执行', "lambda": u'函数', "print": u'打印', "with": u'伴隨',
            "yield": u'产生', "int": u'整数', "str": u'字符串', "range": u'范围',
            "sys": u'系统', "math": u'数学',
            # Add common operators and symbols that might be part of words/identifiers
            "=": "=", "+": "+", "-": "-", "*": "*", "/": "/", "%": "%",
            "(": "(", ")": ")", "[": "[", "]" : "]", "{": "}",
            ".": ".", ",": ",", ":": ":"
        }

        # Chinese to English keywords (for Chinese -> English transpilation)
        self.zh_to_en_keywords = {v: k for k, v in self.en_to_zh_keywords.items()}

        # Regex to detect Unicode-escaped Chinese identifiers (e.g., _u4f60_u597d)
        self.unicode_name_pattern = re.compile(r'_u[0-9a-fA-F]{4}(?:_u[0-9a-fA-F]{4})*')
        
        # Pre-compile regex patterns for identifying string literals (used for passing through unchanged)
        self._string_patterns = [
            re.compile(r'(?:[fFrRbu])?"""(?:.|\n)*?"""', re.DOTALL),
            re.compile(r"(?:[fFrRbu])?'''(?:.|\n)*?'''", re.DOTALL),
            re.compile(r'(?:[fFrRbu])?"(?:\\.|[^"\n\\])*"'),
            re.compile(r"(?:[fFrRbu])?'(?:\\.|[^'\n\\])*'")
        ]

        # Define common fixed operators/delimiters that should never be translated or parsed as identifiers
        # Prioritize multi-character operators first in this list
        self._fixed_operators_list = [
            re.escape(op) for op in [
                '==', '!=', '<=', '>=', '+=', '-=', '*=', '/=', '%=',
                '**=', '//=', '&=', '|=', '^=', '>>=', '<<=', '->', '...', '**',
                # Single char operators/delimiters - escape them too
                '+', '-', '*', '/', '%', '<', '>', '=', '!', '&', '|', '^', '~',
                ',', '(', ')', '[', ']', '{', '}', '.', ':', '@'
            ]
        ]
        self._fixed_operators_regex = re.compile('|'.join(self._fixed_operators_list))

        # Compile a single regex for all English keywords for the *post-AST translation*
        all_en_keywords = sorted(self.en_to_zh_keywords.keys(), key=len, reverse=True)
        self._all_en_keywords_regex = re.compile(r'\b(?:' + '|'.join(re.escape(k) for k in all_en_keywords) + r')\b')


    def _is_chinese_char(self, char):
        """
        Check if a character is a Chinese character (has a Unicode ordinal > 255).
        """
        return ord(char) > 255

    def _to_unicode_name(self, word):
        """
        Translates a Chinese word into a valid Python identifier using
        its Unicode code points. For example, '你好' becomes '_u4f60_u597d'.
        """
        return ''.join(f'_u{ord(char):x}' for char in word)

    def _from_unicode_name(self, unicode_name):
        """
        Converts a Unicode-escaped identifier (e.g., '_u4f60_u597d') back to Chinese characters.
        """
        if not unicode_name.startswith('_u'):
            return unicode_name # Not a unicode-escaped name

        parts = unicode_name.split('_u')
        decoded_chars = []
        for part in parts:
            if part: # Skip empty string at the beginning
                try:
                    decoded_chars.append(chr(int(part, 16)))
                except ValueError:
                    return unicode_name # Malformed, return original

        return ''.join(decoded_chars)

    def _initial_token_pass(self, content, direction="zh_to_en"):
        """
        Performs an initial tokenization and simple replacement pass.
        For zh_to_en: Translates Chinese keywords and converts raw Chinese identifiers to _uXXXX.
        For en_to_zh: Passes all English keywords and identifiers *as-is* to ensure valid Python for AST parsing.
        Strings, comments, whitespace, and operators are always preserved as-is.
        """
        patterns = []

        # 1. Highest priority: string literals (multi-line then single-line)
        patterns.extend([p.pattern for p in self._string_patterns])

        # 2. Second highest: comments
        patterns.append(r"#[^\n]*(?:\n|$)")
        
        # 3. Third highest: whitespace (crucial for preserving layout for AST parsing)
        patterns.append(r"\s+")

        # 4. Fourth highest: all fixed operators (multi-char then single-char)
        patterns.append(self._fixed_operators_regex.pattern)

        # 5. Keywords and Identifiers (order within this section matters for specificity)
        if direction == "zh_to_en":
            # For Chinese to English: Prioritize Chinese keywords, then _uXXXX, then raw Chinese, then English identifiers
            sorted_zh_keywords = sorted(self.zh_to_en_keywords.keys(), key=len, reverse=True)
            patterns.append(r'\b(?:' + '|'.join(re.escape(k) for k in sorted_zh_keywords) + r')\b')
            patterns.append(self.unicode_name_pattern.pattern) # _uXXXX identifiers
            patterns.append(r'[\u4e00-\u9fff]+') # Raw Chinese chars (should mostly be covered by unicode_name_pattern if already processed)
            patterns.append(r'[a-zA-Z_][a-zA-Z0-9_]*') # Standard English identifiers
        else: # direction == "en_to_zh"
            # For English to Chinese: Pass all English keywords and identifiers as-is.
            # They will be translated in the _post_ast_keyword_translation step.
            patterns.append(r'[a-zA-Z_][a-zA-Z0-9_]*') # Matches all English alphanumeric words
        
        # 6. Numbers (lowest priority as they are very specific)
        patterns.append(r'\d+(?:\.\d*)?')

        # Compile the regex with DOTALL flag
        token_pattern = re.compile('|'.join(patterns), re.DOTALL)
        
        processed_tokens = []
        for match in token_pattern.finditer(content):
            token = match.group(0)
            
            # --- Pass-through tokens (must be preserved exactly and not translated) ---
            if any(p.fullmatch(token) for p in self._string_patterns): # String literals
                processed_tokens.append(token)
            elif token.startswith('#'): # Comments
                processed_tokens.append(token)
            elif re.fullmatch(r"\s+", token): # Whitespace
                processed_tokens.append(token)
            elif self._fixed_operators_regex.fullmatch(token): # All fixed operators (multi and single char)
                processed_tokens.append(token)
            elif re.fullmatch(r'\d+(?:\.\d*)?', token): # Numbers
                processed_tokens.append(token)
            
            # --- Translation logic for keywords and identifiers ---
            elif direction == "zh_to_en":
                if token in self.zh_to_en_keywords: # Chinese keyword to English
                    processed_tokens.append(self.zh_to_en_keywords[token])
                elif self.unicode_name_pattern.fullmatch(token): # _uXXXX identifier (keep for AST decoding later)
                    processed_tokens.append(token)
                elif any(self._is_chinese_char(char) for char in token): # Raw Chinese identifier (convert to _uXXXX)
                    processed_tokens.append(self._to_unicode_name(token))
                elif re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", token): # Standard English identifier (keep as is for AST)
                    processed_tokens.append(token)
                else:
                    # Fallback for anything else (should ideally not be hit for valid code)
                    processed_tokens.append(token)
            else: # en_to_zh
                # English keywords and identifiers are passed as-is to ast.parse()
                # Their translation to Chinese equivalents happens in _post_ast_keyword_translation.
                # Identifiers are NOT converted to _uXXXX in this direction.
                processed_tokens.append(token)
        
        return "".join(processed_tokens)


    class ASTConverter(ast.NodeTransformer):
        """
        AST NodeTransformer to apply translations to identifiers within the AST.
        """
        def __init__(self, transpiler_instance, direction):
            self.transpiler = transpiler_instance
            self.direction = direction
            super().__init__()

        def visit_Name(self, node):
            """
            Visits Name nodes (identifiers) to apply translation.
            For zh_to_en: Decodes _uXXXX identifiers back to Chinese characters.
            For en_to_zh: Does NOT convert English identifiers to _uXXXX; they remain English.
            """
            original_id = node.id
            translated_id = original_id

            if self.direction == "zh_to_en":
                # Only decode if it's a unicode-encoded name
                if self.transpiler.unicode_name_pattern.fullmatch(original_id):
                    translated_id = self.transpiler._from_unicode_name(original_id)
            elif self.direction == "en_to_zh":
                # Do NOT convert English identifiers to _uXXXX here.
                # They are meant to remain English in the final Chinese output.
                pass # No operation, simply return the node as-is.
            
            # Update the node's id if it was translated (only applicable for zh_to_en here)
            if translated_id != original_id:
                node.id = translated_id
            
            return node

        def visit_Constant(self, node):
            """
            Visits Constant nodes (including strings, numbers, None, True, False).
            Ensures string literals are NOT translated. Python 3.8+ uses Constant.
            """
            if isinstance(node.value, str):
                # This is a string literal (e.g., "hello", """docstring""")
                # We do NOT translate the content of string literals.
                return node
            
            return self.generic_visit(node) # Continue visiting children for other constant types

        def visit_Str(self, node):
            """
            Visits Str nodes (string literals for Python < 3.8).
            Ensures string literals are NOT translated.
            """
            return node # Do not translate string literal content
        
        # We generally do not need to visit other nodes like imports, functions etc. here
        # because the keywords themselves (e.g. 'def', 'import') are handled
        # in the _post_ast_keyword_translation step (for en_to_zh) or initial_token_pass (for zh_to_en)
        # and not as 'Name' nodes in the AST for structural elements.


    def _post_ast_keyword_translation(self, content):
        """
        Performs a final pass to translate English Python keywords to Chinese
        after AST unparsing. This ensures correct syntax for ast.parse()
        and the desired Chinese keywords in the output.
        """
        translated_content_tokens = []
        
        # Regex to match:
        # 1. String literals (to avoid translating keywords within strings)
        # 2. _uXXXX identifiers (to avoid translating parts of them)
        # 3. All English keywords (the targets for translation)
        # 4. Any other text (pass through)
        
        # Combine string patterns, unicode names, and keyword patterns
        patterns = [p.pattern for p in self._string_patterns]
        patterns.append(self.unicode_name_pattern.pattern)
        patterns.append(self._all_en_keywords_regex.pattern) # All English keywords
        patterns.append(r'\s+') # Whitespace
        patterns.append(r'[^\s]+') # Any other non-whitespace characters (fallback)

        final_pass_regex = re.compile('|'.join(patterns), re.DOTALL)

        for match in final_pass_regex.finditer(content):
            token = match.group(0)
            
            # Check if it's a string or _uXXXX identifier (pass through)
            if any(p.fullmatch(token) for p in self._string_patterns) or \
               self.unicode_name_pattern.fullmatch(token):
                translated_content_tokens.append(token)
            # Check if it's an English keyword that needs translation
            elif self._all_en_keywords_regex.fullmatch(token) and token in self.en_to_zh_keywords:
                translated_content_tokens.append(self.en_to_zh_keywords[token])
            else:
                translated_content_tokens.append(token) # Pass through other tokens (whitespace, operators, numbers, etc.)
        
        return "".join(translated_content_tokens)


    def transpile_zh_to_en(self, chinese_code):
        """
        Transpiles Chinese Python code to English Python code using AST.
        """
        # 1. Initial pass: translate Chinese keywords to English and
        #    convert raw Chinese identifiers to _uXXXX for AST parsing.
        intermediate_python_code = self._initial_token_pass(chinese_code, direction="zh_to_en")
        
        # 2. Parse the intermediate code into an AST
        try:
            tree = ast.parse(intermediate_python_code)
        except SyntaxError as e:
            print(f"SyntaxError during AST parsing (zh_to_en intermediate code):\n{intermediate_python_code}")
            raise e
        
        # 3. Transform the AST to decode _uXXXX identifiers back to Chinese characters
        converter = self.ASTConverter(self, "zh_to_en")
        new_tree = converter.visit(tree)
        
        # 4. Unparse the AST back into English Python code
        return ast.unparse(new_tree)

    def transpile_en_to_zh(self, english_code):
        """
        Transpiles English Python code to Chinese Python code using AST.
        """
        # 1. Initial pass: All English keywords and identifiers are passed
        #    as-is to produce valid English Python for AST parsing.
        intermediate_python_code_for_ast = self._initial_token_pass(english_code, direction="en_to_zh")
        
        # 2. Parse the intermediate code into an AST
        try:
            tree = ast.parse(intermediate_python_code_for_ast)
        except SyntaxError as e:
            print(f"SyntaxError during AST parsing (en_to_zh intermediate code):\n{intermediate_python_code_for_ast}")
            raise e
        
        # 3. Transform the AST: English identifiers are NOT converted to _uXXXX.
        #    This step essentially performs no identifier transformation for en_to_zh now.
        converter = self.ASTConverter(self, "en_to_zh")
        new_tree = converter.visit(tree)
        
        # 4. Unparse the AST back into English Python code.
        #    This output will have English keywords (e.g., 'def', 'import') and English identifiers.
        english_code_with_original_ids = ast.unparse(new_tree)

        # 5. Final post-AST pass: Replace English keywords with Chinese equivalents.
        final_chinese_code = self._post_ast_keyword_translation(english_code_with_original_ids)
        
        return final_chinese_code


def main_chinese_to_english():
    """
    Main function for Chinese to English transpilation.
    """
    if len(sys.argv) != 3:
        print("Usage: python chython_extended.py <source_chinese_file> <target_english_file> zh_to_en")
        sys.exit(1)

    source_file_path = sys.argv[1]
    target_file_path = sys.argv[2]
    
    transpiler = Transpiler()

    try:
        with codecs.open(source_file_path, encoding='utf-8', mode='r') as chinese_source:
            chinese_code = chinese_source.read()
        
        english_code = transpiler.transpile_zh_to_en(chinese_code)

        with open(target_file_path, 'w', encoding='utf-8') as english_target:
            english_target.write(english_code)
        
        print(f"Successfully transpiled Chinese from '{source_file_path}' to English in '{target_file_path}'.")

    except FileNotFoundError:
        print(f"Error: The file '{source_file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}. Please ensure your Python version is 3.9+ for ast.unparse().")
        import traceback
        traceback.print_exc() # Print full traceback for debugging

def main_english_to_chinese():
    """
    Main function for English to Chinese transpilation.
    """
    if len(sys.argv) != 3:
        print("Usage: python chython_extended.py <source_english_file> <target_chinese_file> en_to_zh")
        sys.exit(1)

    source_file_path = sys.argv[1]
    target_file_path = sys.argv[2]
    
    transpiler = Transpiler()

    try:
        with codecs.open(source_file_path, encoding='utf-8', mode='r') as english_source:
            english_code = english_source.read()
        
        chinese_code = transpiler.transpile_en_to_zh(english_code)

        with open(target_file_path, 'w', encoding='utf-8') as chinese_target:
            chinese_target.write(chinese_code)
        
        print(f"Successfully transpiled English from '{source_file_path}' to Chinese in '{target_file_path}'.")

    except FileNotFoundError:
        print(f"Error: The file '{source_file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}. Please ensure your Python version is 3.9+ for ast.unparse().")
        import traceback
        traceback.print_exc() # Print full traceback for debugging


if __name__ == '__main__':
    if len(sys.argv) == 4:
        direction = sys.argv[3]
        # Remove the direction argument for the main functions' sys.argv expectation
        sys.argv = sys.argv[:3] 
        if direction == "en_to_zh":
            print("Running English to Chinese Transpilation (using AST)...")
            main_english_to_chinese()
        elif direction == "zh_to_en":
            print("Running Chinese to English Transpilation (using AST)...")
            main_chinese_to_english()
        else:
            print("Invalid direction specified. Use 'en_to_zh' or 'zh_to_en'.")
            sys.exit(1)
    else:
        print("Please specify transpilation direction: 'en_to_zh' or 'zh_to_en' as a third argument.")
        print("Example: python chython_extended.py input.en.py output.zh.py en_to_zh")
        sys.exit(1)
