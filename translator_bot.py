#!/usr/bin/env python3

import sys

# Assuming your lib directory is at /home/impotepus/telebots/aihelper/lib
# Adjust the path as necessary
sys.path.append('/home/impotepus/aihelper/lib')

from lib.telegram.bots.translator_bot import TranslatorBot

def main():
    bot = TranslatorBot()
    bot.run()

if __name__ == "__main__":
    main()
