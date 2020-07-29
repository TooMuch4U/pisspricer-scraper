import tools
import os
import sys
from abc import ABC, abstractmethod


class Store(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def update_all_items(self):
        pass

    @staticmethod
    def print_progress(iteration, total, title=""):
        os.system('clear')

        # Set length for either side of title
        length = 50
        dash_n = len('Progress:' + 'Complete') + length - len(title)
        if dash_n % 2 == 0:
            dash_l = dash_r = dash_n // 2
        else:
            dash_l = dash_r = dash_n // 2
            dash_l += 1

        # Print Title
        print(dash_l * "-" + title + dash_r * "-")
        sys.stdout.flush()


        # Print bar
        tools.print_progress_bar(iteration, total, prefix='Progress:', suffix='Complete', length=length)




