# The Royal Game of Ur: The Classic Version

Code for playing analyzing and exploring the Royal Game of Ur (classic rules).

Read about the game and code at <https://jheled.github.io/royalur/>.

## Installation

Both the distribution and Github are missing the database file, as the current repo
doesn't have LFS enabled. If you want to run with Ishtar (and you do),
download the file and place it in the 'royalur/data' directory.

>>> cd royalur/data; wget https://filedn.com/llztAlmJ0zvkPa8QEheU5n5/db16.bin

When installing the project's wheel, by default no additional dependencies are installed.
This is sufficient to execute the core library. To run the GUI application on any system,
the Pillow package needs to be installed. To run the command-line
curses-based application on Windows, the windows-curses package needs to be installed.
