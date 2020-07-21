import sublime
import sublime_plugin
import math

DRAGON_WORDS_PANEL_NAME = "DragonWords"
WORD_ID_FIRST_LETTERS = 'lpmrtsgyf'

PanelWords = {}


def is_dragon_words_view(view):
    return view.name() == DRAGON_WORDS_PANEL_NAME


def generate_word_id():
    for first_letter in WORD_ID_FIRST_LETTERS:
        for second_letter in 'abcdefghijklmnopqrstuvwxyz':
            yield first_letter + second_letter


def create_panel(window):
    active_group = window.active_group()
    window.set_layout({"cols": [0.0, 1.0], "rows": [0.0, 0.8, 1.0], "cells": [[0, 0, 1, 1], [0, 1, 1, 2]]})
    window.focus_group(1)
    view = window.new_file()
    view.set_scratch(True)
    view.set_name(DRAGON_WORDS_PANEL_NAME)
    view.set_read_only(True)
    window.focus_group(active_group)
    return view


def find_panel(window):
    for view in window.views():
        if is_dragon_words_view(view):
            return view
    return None


def is_panel_visible(window, view):
    return view == window.active_view_in_group(1)


def show_panel(window):
    view = find_panel(window)
    if not view:
        create_panel(window)
    else:
        window.focus_view(view)
        window.focus_group(0)


def hide_panel(window):
    active_group = window.active_group()
    view = find_panel(window)
    if view:
        view.close()
    window.focus_group(active_group)
    if not window.views_in_group(1):
        window.set_layout({"cols": [0.0, 1.0], "rows": [0.0, 1.0], "cells": [[0, 0, 1, 1]]})


def construct_words(view):
    word_id = generate_word_id()
    auto_complete_items = view.settings().get('auto_complete_items')
    if auto_complete_items:
        return {next(word_id): text for text in auto_complete_items}
    return {}


def save_words(panel_view, words):
    panel_id = panel_view.id()
    PanelWords[panel_id] = words


def get_words(panel_view):
    return PanelWords.get(panel_view.id(), {})


def render_words(edit, panel_view, words):
    panel_width = math.floor(panel_view.viewport_extent()[0] / panel_view.em_width()) - 1
    panel_height = math.floor(panel_view.viewport_extent()[1] / panel_view.line_height()) - 1
    word_id_length = len(next(generate_word_id()))
    longest_word_length = max(len(w) for w in words.values()) if words else 0
    column_width = longest_word_length + 5 + word_id_length
    column_count = math.floor(panel_width / column_width)
    line_count = math.ceil(len(words) / column_count)

    text_items = [k + ' ' + v + ' ' * (column_width - len(v) - 1 - len(k)) for k, v in words.items()]
    text = ""
    for row in range(line_count):
        i = row * column_count
        text += "".join(text_items[i:i+column_count]) + "\n"

    panel_view.set_read_only(False)
    panel_view.erase(edit, sublime.Region(0, panel_view.size()))
    panel_view.insert(edit, 0, text)
    panel_view.set_read_only(True)


class DragonWordsUpdatePanelCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        window = self.view.window()
        if not window:
            return

        panel_view = find_panel(window)
        if not panel_view:
            return

        words = construct_words(self.view)
        save_words(panel_view, words)
        render_words(edit, panel_view, words)


class DragonWordsToggleSidebarCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = find_panel(self.window)
        if view and is_panel_visible(self.window, view):
            hide_panel(self.window)
        else:
            show_panel(self)


class DragonWordsUseWord(sublime_plugin.TextCommand):
    def run(self, edit):
        def insert_text(letters):
            if is_dragon_words_view(view):
                return

            panel_view = find_panel(window)
            words = get_words(panel_view)
            word = words.get(letters, None)

            if not word:
                return

            if view.settings().has("terminus_view"):
                window.run_command('terminus_send_string', args={"string": word})
            else:
                view.run_command('insert_snippet', args={"contents": word})

            # # Make a copy of the regions in the current selection
            # regions = []
            # sel = self.view.sel()
            # for region in sel:
            #     regions.append(region)

            # for region in regions:
            #     self.view.replace(edit, region, word)

        view = self.view
        window = self.view.window()
        window.show_input_panel("Letters:", "", insert_text, None, None)


class DragonWordsEvenListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        if is_dragon_words_view(view):
            return

        view.run_command('dragon_words_update_panel')

    def on_modified_async(self, view):
        if is_dragon_words_view(view):
            return

        view.run_command('dragon_words_update_panel')


