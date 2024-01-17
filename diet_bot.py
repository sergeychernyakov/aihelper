#!/usr/bin/env python3

import sys

# Adjust the path as necessary
sys.path.append('/home/impotepus/aihelper/lib')

from lib.telegram.bots.diet_bot import DietBot

def main():
    bot = DietBot()
    bot.run()

if __name__ == "__main__":
    main()
