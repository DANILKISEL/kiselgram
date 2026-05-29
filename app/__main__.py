import colorama
from colorama import Fore, Style
from pathlib import Path
import sys

if __name__ == "__main__":
    file_path = Path(__file__).resolve()
    root_folder_name = "app"

    if root_folder_name in file_path.parts:
        root_idx = file_path.parts.index(root_folder_name)
        # Get all parts from the root folder up to the file name
        module_parts = list(file_path.parts[root_idx:-1])

        # Avoid adding '__main__' or '__init__' to the final path string
        if file_path.stem not in ("__main__", "__init__"):
            module_parts.append(file_path.stem)

        mod_name = ".".join(module_parts)
    else:
        mod_name = file_path.stem
else:
    # If imported normally, use __name__
    mod_name = __name__

# 2. Safety check for edge cases where __name__ itself contains '__main__'
if mod_name.endswith(".__main__"):
    mod_name = mod_name.rsplit(".__main__", 1)[0]

colorama.init()

print(Style.BRIGHT + "\033[38;5;208m" + """
  ____      __ __ _________ ________    __________  ___    __  ___   ____
 / / /     / //_//  _/ ___// ____/ /   / ____/ __ \/   |  /  |/  /   \\ \\ \\
/ / /     / ,<   / / \__ \/ __/ / /   / / __/ /_/ / /| | / /|_/ /     \\ \\ \\
\ \ \    / /| |_/ / ___/ / /___/ /___/ /_/ / _, _/ ___ |/ /  / /      / / /
 \_\_\  /_/ |_/___//____/_____/_____/\____/_/ |_/_/  |_/_/  /_/      /_/_/

""" + Style.RESET_ALL + Fore.RESET)

print(Style.BRIGHT + Fore.RED + "The module " + mod_name + " is not runnable" + Fore.RESET + Style.RESET_ALL )




