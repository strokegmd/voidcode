from pathlib import Path

def main() -> None:
    count = 0
    for path in Path('..').rglob('*'):
        if not path.is_file() or '__pycache__' in str(path) or '.wasm' in str(path):
            continue

        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
            print(path)
            print(content)

            lines = content.splitlines()
            count += len(lines)
    
    print(f'[*] total project line count: {count}')

if __name__ == '__main__':
    main()
