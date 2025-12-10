
import akshare as ak

# List all attributes of akshare to find relevant functions
for name in dir(ak):
    if any(keyword in name.lower() for keyword in ["predict", "prob", "future", "watch"]):
        print(name)
