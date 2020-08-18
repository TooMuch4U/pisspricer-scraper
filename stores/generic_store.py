import tools
import os
from abc import ABC, abstractmethod


class Store(ABC):

    @abstractmethod
    def update_all_items(self):
        pass

    @abstractmethod
    def update_locations(self):
        pass

    @staticmethod
    def print_progress(iteration, total, title=""):
        """
        Print progress bar
        :param iteration: Iteration number
        :param total: Total number of iterations there will be
        :param title: Title to print on iteration zero
        :return: None
        """
        length = 50

        # Print Title
        if iteration == 0:
            dash_n = len('Progress:' + 'Complete') + length - len(title)
            if dash_n % 2 == 0:
                dash_l = dash_r = dash_n // 2
            else:
                dash_l = dash_r = dash_n // 2
                dash_l += 1
            os.system('clear')
            print(dash_l * "-" + title + dash_r * "-")

        # Print bar
        tools.print_progress_bar(iteration, total, prefix='Progress:', suffix='Complete', length=length)




