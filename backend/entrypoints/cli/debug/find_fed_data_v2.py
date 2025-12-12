
import akshare as ak

# List all attributes of akshare to find relevant functions
for name in dir(ak):
    if "macro" in name.lower() and "usa" in name.lower():
        print(name)
