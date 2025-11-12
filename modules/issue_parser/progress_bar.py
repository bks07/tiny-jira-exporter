
import math

class ProgressBar:
    """
    This class contains methods to display a progress bar while parsing issues.
    """
    def __init__(
        self,
        total_number_of_items: int,
        length: int = 10
    ) -> None:
        """
        Initialize the ProgressBar instance.
        """
        self.__total_number_of_items = total_number_of_items
        self.__current_item_index = 0
        self.__length = length

    def next_item(
        self,
    ) -> None:
        """
        Update the progress bar display.

        :param total_number_of_items: The total number of items to process
        :type total_number_of_items: int
        :param current_item_index: The current index of the item being processed
        :type current_item_index: int
        :param item_id: The id of the currently processed item - will be printed as well
        :type item_id: str
        :param item_key: The key of the currently processed item - will be printed as well
        :type item_key: str
        :param item_summary: The summary of the currently processed item - will be printed as well
        :type item_summary: str
        
        :return: None
        """
        self.__current_item_index += 1

    def display(
        self,
        message: str
    ) -> None:
        """
        This method prints out a progress bar while the issues get parsed.

        :param number_of_issues: The total number of fetched issues to parse
        :type number_of_issues: int
        :param iterator: Keeps track which of the fetched issues is currently parsed
        :type iterator: int
        :param issue_id: The id of the currently parsed issue - will be printed as well
        :type issue_id: str
        :param issue_key: The key of the currently parsed issue - will be printed as well
        :type issue_key: str
        :param issue_summary: The summary of the currently parsed issue - will be printed as well
        :type issue_summary: str
        
        :return: None
        """
        percentage = math.ceil(self.__current_item_index/self.__total_number_of_items*100)

        length_done = int(percentage / self.__length)
        length_todo = self.__length - length_done

        progress_bar_done = "#" * length_done
        progress_bar_todo = " " * length_todo

        progress_bar = "[" + progress_bar_done + progress_bar_todo + "]"
        
        # Strip length to avoid malfunction SKSD-54
        if len(message) > 32:
            message = message[:29].strip() + "..."

        end_of_print = "\r"
        if percentage == 100:
            end_of_print = "\n"

        print(f" {progress_bar} {self.__current_item_index}/{self.__total_number_of_items} ({percentage}%) {message}", end=end_of_print)
        if percentage < 100:
            print("\033[2K", end="") # Clear entire line