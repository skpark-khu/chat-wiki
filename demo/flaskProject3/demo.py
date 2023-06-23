def count_characters(filename):
    try:
        with open(filename, 'r') as file:
            text = file.read()
            character_count = len(text)
            return character_count
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        return 0

# Example usage
file_path = 'path/to/your/file.txt'  # Replace with the actual file path
count = count_characters(file_path)
print(f"Number of characters in the file: {count}")