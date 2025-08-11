# Chython Extended - Two-Way Python-Chinese Transpiler

## About

**Chython Extended** is a significant refactor and advancement of the original "Chython - Python in Chinese" project. Its core mission remains to make Python programming more accessible to non-English native speakers, specifically focusing on Chinese.

While the original project demonstrated the feasibility of writing Python code using Chinese keywords, Chython Extended transforms this concept into a more robust and practical **two-way transpiler**. I've moved beyond simple word-by-word replacement to leverage Python's **Abstract Syntax Tree (AST)**, ensuring that the structural integrity and readability of the code are preserved across translations.

This refactor aims to provide a more reliable and extensible foundation for a truly localized programming experience.

-----

## Features

  * **Bidirectional Transpilation**:
      * **English Python to Chinese Python**: Translate your standard English Python code into a version where core Python keywords (like `if`, `def`, `import`, `True`) are replaced with their Chinese equivalents (e.g., `如果`, `定义`, `导入`, `真`). Critically, **English variable names, function names, and module names are preserved in English** for clarity and compatibility.
      * **Chinese Python to English Python**: Convert your Chinese Python code back into standard English Python, including translating Chinese keywords back and encoding Chinese identifiers into unique `_uXXXX` forms (e.g., `_u4f60_u597d` for "你好") for full compatibility and round-tripping.
  * **AST-Based Robustness**: By utilizing Python's `ast` library, the transpiler understands the underlying **grammatical structure** of your code. This eliminates common issues found in simpler regex-based approaches, ensuring:
      * **Accurate Keyword Translation**: Keywords are correctly identified based on their syntactic role, preventing accidental translation of words within strings or comments.
      * **Preservation of Code Structure**: Indentation, multi-line statements, and complex expressions are handled natively by the AST parser and unparser, resulting in clean, syntactically valid output.
      * **Correct Handling of String Literals**: Docstrings, f-strings, and other string literals are identified and passed through without their internal content being translated or corrupted.
  * **Improved Identifier Handling**: English identifiers in the Chinese output remain in English, improving readability and integration with existing libraries. Chinese identifiers in the English output are converted to `_uXXXX` for universal compatibility.

-----

## Limitations

As with any complex language tool, Chython Extended has some limitations:

  * **Comment Removal**: Due to the inherent design of Python's `ast` module, **comments (`#`) are not included in the Abstract Syntax Tree**. This means that any comments in your source code will be **removed** during the transpilation process.
  * **Subset of Python**: Only a translated subset of Python's vast standard library and core language features are currently supported.
  * **Grammatical Nuances**: While keyword translation is improved, some Chinese grammar structures might still feel a bit "stilted" as the primary goal remains functional transpilation rather than perfectly natural Chinese prose.

-----

## Running It

Chython Extended uses a Python script to perform the two-way translation.

1.  **Translation Process**:
      * The script reads your source Python file (either English or Chinese).
      * It performs an initial tokenization pass to handle simple keyword translations and prepare for AST parsing.
      * The code is then parsed into an Abstract Syntax Tree (AST).
      * The AST is transformed to handle identifier conversions (e.g., `_uXXXX` encoding/decoding for Chinese identifiers in English output).
      * Finally, the transformed AST is unparsed back into a Python string. For English-to-Chinese, a **post-AST pass** then translates the remaining English keywords into Chinese.
2.  **Output**: A new `.py` file is created with the transpiled code in the specified target language.
3.  **Execution**: The generated `.py` file can then be run directly with a standard Python interpreter.

### **Usage**

To run the transpiler, use the following command structure:

```bash
python chython_extended.py <source_file> <target_file> <direction>
```

  * `<source_file>`: The path to your input Python file (e.g., `my_script.en.py` or `my_script.zh.py`).
  * `<target_file>`: The desired path for the output transpiled file (e.g., `my_script.zh.py` or `my_script.en.py`).
  * `<direction>`: Specify the transpilation direction:
      * `en_to_zh`: To translate **English Python to Chinese Python**.
      * `zh_to_en`: To translate **Chinese Python to English Python**.

**Example: Translating English to Chinese**

```bash
python chython_extended.py input.en.py output.zh.py en_to_zh
```

**Example: Translating Chinese back to English**

```bash
python chython_extended.py output.zh.py final_output.en.py zh_to_en
```
