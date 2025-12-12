
import akshare as ak

# List all attributes of akshare to find relevant functions
for name in dir(ak):
    if "cme" in name.lower() or "watch" in name.lower():
        print(name)
