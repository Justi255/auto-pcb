import os

def get_folder_size(folder_path):
    total_size = 0
    subfolder_sizes = {}

    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            total_size += os.path.getsize(file_path)

        if root == folder_path:
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                subfolder_sizes[dir_name] = get_folder_size(dir_path)[0]

    return total_size, subfolder_sizes

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def main():
    folder_path = '.'  # 设置你要统计的目录路径
    total_size, subfolder_sizes = get_folder_size(folder_path)

    print(f"{'Folder':<30}{'Size':<15}")
    print('-' * 45)
    print(f"{folder_path:<30}{format_size(total_size):<15}")
    for subfolder, size in subfolder_sizes.items():
        print(f"{subfolder:<30}{format_size(size):<15}")

if __name__ == "__main__":
    main()
