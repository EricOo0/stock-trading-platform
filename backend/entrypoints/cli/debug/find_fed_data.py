
import akshare as ak
import inspect

# List all attributes of akshare to find relevant functions
for name in dir(ak):
    if "fed" in name.lower() and "rate" in name.lower():
        print(name)
