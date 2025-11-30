
import math

class ProgressBar:
    """
    Display a dynamic console progress bar for tracking long-running operations.

    Provides real-time visual feedback during iterative processes like issue parsing,
    data fetching, or file processing by showing completion percentage, visual progress
    indicator, item counts, and contextual status messages. The progress bar automatically
    handles dynamic line updates, formatting, and console cleanup for professional output.

    The progress bar uses ANSI escape sequences for line clearing and carriage returns
    for dynamic updates, providing smooth progress visualization without scrolling.
    Messages are automatically truncated to prevent display formatting issues on
    narrow terminals.

    Format: [####      ] 42/100 (42%) Processing current item...

    Example:
        >>> # Basic usage for file processing
        >>> progress = ProgressBar(total_number_of_items=150)
        >>> for i, item in enumerate(items):
        ...     progress.next_item()
        ...     progress.display(f"Processing {item.name}")
        
        >>> # Usage with Jira issue processing
        >>> progress = ProgressBar(total_number_of_items=len(issues))
        >>> for issue in issues:
        ...     progress.next_item()
        ...     progress.display(f"Parsing {issue['key']}")

    Attributes:
        __total_number_of_items (int): Total number of items to process.
        __current_item_index (int): Current position in the processing sequence.
        __length (int): Visual length of the progress bar in characters.

    Note:
        The progress bar is designed for terminal output and may not display
        correctly in environments that don't support ANSI escape sequences.
    """
    def __init__(
        self,
        total_number_of_items: int,
        length: int = 10
    ) -> None:
        """
        Initialize a new ProgressBar instance with specified parameters.

        Sets up the progress tracking state and visual parameters for dynamic
        console display. The progress tracking starts at zero and will advance
        to the specified total through next_item() calls.

        The length parameter controls the visual width of the progress indicator
        (the [####    ] portion), while the total display width includes
        additional space for percentages, counts, and status messages.

        Args:
            total_number_of_items (int): Total number of items that will be processed.
                                        Must be greater than 0 for meaningful progress display.
            length (int): Visual length of the progress bar indicator in characters.
                         Default is 10, which provides good balance between detail and space.

        Example:
            >>> # Standard progress bar
            >>> progress = ProgressBar(total_number_of_items=100)
            
            >>> # Longer progress bar for more granular visual feedback
            >>> progress = ProgressBar(total_number_of_items=1000, length=20)
        """
        self.__total_number_of_items = total_number_of_items
        self.__current_item_index = 0
        self.__length = length

    def next_item(
        self,
    ) -> None:
        """
        Advance the progress counter to the next item in the sequence.

        Increments the internal item counter to reflect that one more item has
        been processed. This method should be called exactly once for each
        completed item, typically at the beginning or end of each iteration
        in a processing loop.

        The progress percentage and visual display are automatically recalculated
        based on the new position relative to the total number of items.

        Note:
            Call this method before display() to show the updated progress.
            Calling this method more times than the total_number_of_items
            will result in percentages exceeding 100%.

        Example:
            >>> for item in items_to_process:
            ...     progress.next_item()  # Increment first
            ...     # Process the item here
            ...     progress.display(f"Processed {item.name}")
        """
        self.__current_item_index += 1

    def display(
        self,
        message: str
    ) -> None:
        """
        Render and display the current progress bar with contextual status message.

        Outputs a formatted progress bar showing visual completion indicator,
        percentage, item counts, and a custom status message. Uses ANSI escape
        sequences for dynamic line updates, creating smooth progress visualization
        without scrolling the terminal.

        The display automatically handles:
        - Dynamic line clearing and updating using carriage returns
        - Message truncation to prevent formatting issues on narrow terminals
        - Final newline output when progress reaches 100% completion
        - Visual progress calculation based on current position

        Display format components:
        - Visual bar: [####      ] (filled # characters, empty spaces)
        - Progress: current_item/total_items (percentage%)
        - Status: custom message (truncated if too long)

        Args:
            message (str): Descriptive status message to show alongside the progress bar.
                          Messages longer than 32 characters are automatically truncated
                          to 29 characters plus "..." to maintain display formatting.

        Example:
            >>> progress.display("Fetching issue data from Jira")
            >>> # Output: [###       ] 3/10 (30%) Fetching issue data from Jira
            
            >>> progress.display("Processing very long item name that exceeds limit")
            >>> # Output: [####      ] 4/10 (40%) Processing very long item...

        Note:
            This method should be called after next_item() to reflect the
            current progress state. The progress bar will show a newline
            and stop updating when 100% completion is reached.
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