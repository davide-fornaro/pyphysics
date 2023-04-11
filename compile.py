import os
import shutil
import time


def main():
    os.system("cls")
    now = time.time()
    os.system("pyinstaller --onefile main.py")
    shutil.rmtree("build")
    os.remove("main.spec")
    print(f"Compiled in {round(time.time() - now, 2)} seconds")
    os.system("start dist")


if __name__ == "__main__":
    main()
