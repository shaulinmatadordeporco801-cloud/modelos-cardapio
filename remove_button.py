
original_file = "main.py"
temp_file = "main_new.py"

with open(original_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

with open(temp_file, "w", encoding="utf-8") as f:
    for line in lines:
        if 'href="https://wa.me/5519989427247"' in line and 'Pedir' in line:
            # Skip this line (effectively removing it)
            continue
        f.write(line)

import os
os.replace(temp_file, original_file)
print("Line removed successfully.")
