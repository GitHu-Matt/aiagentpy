'''
#1 tests.py (project root)
from functions.get_files_info import get_files_info

def print_test(title, working_directory, directory):
    result = get_files_info(working_directory, directory)
    print(title)
    if result.startswith("Error:"):
        print("\t" + result)   # print error with indentation
    else:
        for line in result.splitlines():
            print("\t" + line)
    print()  # blank line for separation

def main():
    # 1) get_files_info("calculator", ".")
    print_test("Result for current directory:", "calculator", ".")

    # 2) get_files_info("calculator", "pkg")
    print_test("Result for 'pkg' directory:", "calculator", "pkg")

    # 3) get_files_info("calculator", "/bin")
    print_test("Result for '/bin' directory:", "calculator", "/bin")

    # 4) get_files_info("calculator", \"../\")
    print_test("Result for '../' directory:", "calculator", "../")

if __name__ == "__main__":
    main()
'''
'''
#2 ch 2 L3, Phase A test 

from functions.get_file_content import get_file_content
from functions.config import MAX_CHARS

def main():
    print("Result for 'lorem.txt' (truncation test):")
    result = get_file_content("calculator", "lorem.txt")
    if result.startswith("Error:"):
        print("\t" + result)
        return

    # Print summary: returned length and whether the truncation marker is present
    print("\tReturned length:", len(result))
    marker = f'[...File "lorem.txt" truncated at {MAX_CHARS} characters]'
    if marker in result:
        print("\tTruncation confirmed (marker found).")
    else:
        print("\tTruncation marker NOT found.")
    # optionally show first 200 characters
    print("\tFirst 200 chars preview:")
    print("\t" + result[:200].replace("\n", "\\n"))

if __name__ == "__main__":
    main()

'''
'''
#3 ch 2 L3, Phase B test

from functions.get_file_content import get_file_content

def print_test(desc, wd, path):
    print(desc)
    result = get_file_content(wd, path)
    if result.startswith("Error:"):
        print("\t" + result)
    else:
        # print a short preview (first 400 chars) for readability
        preview = result[:400]
        if len(result) > 400:
            preview = preview + "..."
        for line in preview.splitlines():
            print("\t" + line)
    print()

def main():
    print_test("get_file_content('calculator', 'main.py'):", "calculator", "main.py")
    print_test("get_file_content('calculator', 'pkg/calculator.py'):", "calculator", "pkg/calculator.py")
    print_test("get_file_content('calculator', '/bin/cat') (should error):", "calculator", "/bin/cat")
    print_test("get_file_content('calculator', 'pkg/does_not_exist.py') (should error):", "calculator", "pkg/does_not_exist.py")

if __name__ == '__main__':
    main()

'''
'''
#4 ch2 L3

from functions.get_file_content import get_file_content

def run_tests():
    print("=== TEST: Truncated lorem.txt ===")
    result = get_file_content("calculator", "lorem.txt")
    print(result[:500])  # show first 500 chars only
    print("...truncated output above...\n")

    print("=== TEST: main.py ===")
    print(get_file_content("calculator", "main.py"), "\n")

    print("=== TEST: pkg/calculator.py ===")
    print(get_file_content("calculator", "pkg/calculator.py"), "\n")

    print("=== TEST: /bin/cat (outside dir) ===")
    print(get_file_content("calculator", "/bin/cat"), "\n")

    print("=== TEST: does_not_exist.py ===")
    print(get_file_content("calculator", "pkg/does_not_exist.py"), "\n")

if __name__ == "__main__":
    run_tests()

'''
'''
# ch2 L4 
# tests.py (project root)
from functions.write_file import write_file

def show(title, result):
    print(title)
    print("\t" + result)
    print()

def main():
    # 1) Overwrite/create a file in the working dir
    r1 = write_file("calculator", "lorem.txt", "wait, this isn't lorem ipsum")
    show('write_file("calculator", "lorem.txt", "..."):', r1)

    # 2) Create a file inside a subdirectory (create parent dirs if needed)
    r2 = write_file("calculator", "pkg/morelorem.txt", "lorem ipsum dolor sit amet")
    show('write_file("calculator", "pkg/morelorem.txt", "..."):', r2)

    # 3) Attempt to write OUTSIDE the working directory (should be blocked)
    r3 = write_file("calculator", "/tmp/temp.txt", "this should not be allowed")
    show('write_file("calculator", "/tmp/temp.txt", "..."):', r3)

if __name__ == "__main__":
    main()

'''

# Ch2 L5
# tests.py (project root) — run-python tests
from functions.run_python import run_python_file

def print_test(title, working_directory, file_path, args=None):
    print(title)
    result = run_python_file(working_directory, file_path, args or [])
    # Print every line indented
    for line in result.splitlines():
        print("\t" + line)
    print()

def main():
    # 1) should print usage/help for calculator
    print_test("1) run_python_file('calculator', 'main.py'):", "calculator", "main.py")

    # 2) should run calculator with expression (rendered output)
    print_test("2) run_python_file('calculator', 'main.py', ['3 + 5']):", "calculator", "main.py", ["3 + 5"])

    # 3) run the calculator's own tests (calculator/tests.py)
    print_test("3) run_python_file('calculator', 'tests.py'):", "calculator", "tests.py")

    # 4) attempt to run a file outside working_directory — should be blocked
    print_test("4) run_python_file('calculator', '../main.py') (should error):", "calculator", "../main.py")

    # 5) nonexistent file (should error)
    print_test("5) run_python_file('calculator', 'nonexistent.py') (should error):", "calculator", "nonexistent.py")

if __name__ == "__main__":
    main()
