
import math

class ProgressBar:
    """
    Display a console progress bar for tracking long-running operations.

    Provides visual feedback during iterative processes like issue parsing by
    showing completion percentage, progress bar visualization, and current item
    information. The progress bar automatically handles line clearing and
    formatting for clean console output.

    Example:
        progress = ProgressBar(total_number_of_items=100)
        for i in range(100):
            progress.next_item()
            progress.display(f"Processing item {i}")

    Attributes:
        __total_number_of_items: Total number of items to process.
        __current_item_index: Current position in the processing sequence.
        __length: Visual length of the progress bar in characters.
    """
    def __init__(
        self,
        total_number_of_items: int,
        length: int = 10
    ) -> None:
        """
        Initialize a new ProgressBar instance.

        Sets up the progress tracking state and visual parameters for the
        progress bar display. The current item index starts at zero.

        Args:
            total_number_of_items: Total number of items to be processed.
            length: Visual length of the progress bar in characters (default: 10).
        """
        self.__total_number_of_items = total_number_of_items
        self.__current_item_index = 0
        self.__length = length

    def next_item(
        self,
    ) -> None:
        """
        Advance the progress counter to the next item.

        Increments the current item index to reflect that one more item has
        been processed. This should be called once for each completed item
        before calling display() to show the updated progress.
        """
        self.__current_item_index += 1

    def display(
        self,
        message: str
    ) -> None:
        """
        Display the current progress bar with status message.

        Renders a visual progress bar showing completion percentage, progress
        visualization, item counts, and a custom status message. The display
        uses carriage returns for dynamic updates and clears the line on
        completion. Long messages are automatically truncated to prevent
        display issues.

        Args:
            message: Status message to display alongside the progress bar.
                   Messages longer than 32 characters are truncated with "...".

        Note:
            The progress bar format: [####      ] 40/100 (40%) Processing item...
        """
        percentage = math.ceil(self.__current_item_index/self.__total_number_of_items*100)

        length_done = int(percentage / self.__length)
        length_todo = self.__length - length_done

        progress_bar_done = "#" * length_done
        progress_bar_todo = " " * length_todo

        progress_bar = "[" + progress_bar_done + progress_bar_todo + "]"
        
        # Strip length to avoid malfunction SKSD-54
        if len(message) > 32:
            message = f"{message[:29].strip()}..."

        end_of_print = "\r"
        if percentage == 100:
            end_of_print = "\n"

        print(f" {progress_bar} {self.__current_item_index}/{self.__total_number_of_items} ({percentage}%) {message}", end=end_of_print)
        if percentage < 100:
            print("\033[2K", end="") # Clear entire line