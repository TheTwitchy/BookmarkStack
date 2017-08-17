import sublime
import sublime_plugin
import uuid

bookmark_stack = []

class StackedBookmark:
    def __init__(self, regions, sheet):
        self.region = regions[0]
        self.sheet = sheet
        self.filename = self.sheet.view().file_name()
        self.id = str(uuid.uuid4())

class BookmarkPushCommand(sublime_plugin.WindowCommand):
    def run(self):
        global bookmark_stack

        tmp_bookmark = StackedBookmark(self.window.active_view().sel(), self.window.active_sheet())

        bookmark_stack.append(tmp_bookmark)

        # Place a gutter marker at the start of the bookmark
        self.window.active_view().add_regions(tmp_bookmark.id, self.window.active_view().sel(), scope="text.plain", icon="circle", flags=sublime.DRAW_NO_FILL|sublime.DRAW_EMPTY_AS_OVERWRITE)
        
        sublime.status_message("Pushed bookmark onto stack")

    def is_enabled(self):
        # Technically will always be available
        return True

# This function needs to be async, which is why it's broken up in such a weird way. Also it's late, and I'm tired.
def focus_to_view(window, view, region, bookmark_id):
    if not view.is_loading():
        # The view is done loading, we can proceed
        # Switch to the correct file
        window.focus_view(view)

        # We're now in the correct file.
        # Jump to the correct region.
        window.active_view().show_at_center(region)
        # Clear the current selection
        window.active_view().sel().clear()
        # Select the bookmarked region
        window.active_view().sel().add(region)

        # Erase the gutter markers
        window.active_view().erase_regions(bookmark_id)

        sublime.status_message("Popped bookmark from stack")

    else:
        # File still not loaded, wait a bit longer
        sublime.set_timeout(lambda:focus_to_view(window, view, region, bookmark_id), 50)

class BookmarkPopCommand(sublime_plugin.WindowCommand):
    def run(self):
        global bookmark_stack

        if len(bookmark_stack) > 0:
            tmp_bookmark = bookmark_stack.pop()

            # Make sure we're in the correct file first...
            if not self.window.active_sheet() is tmp_bookmark.sheet:
                switch_to_view = self.window.find_open_file(tmp_bookmark.filename)

                # Figure out if the file is currently open, it may have been closed
                if switch_to_view == None:
                    # The file isn't open, open it
                    switch_to_view = self.window.open_file(tmp_bookmark.filename)
                    sublime.set_timeout(lambda:focus_to_view(self.window, switch_to_view, tmp_bookmark.region, tmp_bookmark.id), 50)
                else:      
                    # We're not in the correct file, but it's open in another tab presumably                  
                    focus_to_view(self.window, switch_to_view, tmp_bookmark.region, tmp_bookmark.id)
            else:
                # We're already in the correct file.
                focus_to_view(self.window, self.window.active_view(), tmp_bookmark.region, tmp_bookmark.id)

    def is_enabled(self):
        return len(bookmark_stack) > 0
