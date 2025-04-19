import os
import requests


import sublime
import sublime_plugin


def setting(name, view, default=None):
    default = sublime.load_settings("Pastebin.sublime-settings").get(name, default)
    return view.settings().get(name, default)


class PastebinShareCommand(sublime_plugin.TextCommand):
    """Create a pastebin and copy the URL in the clipboard.

    > https://pastebin.com/doc_api
    """

    def run(self, edit, selection=False):
        paste_name = self.view.file_name()
        if paste_name is not None:
            paste_name = os.path.basename(paste_name)
        else:
            paste_name = "Untitled"

        langs = {"js": "javascript", "html": "html5"}
        syntax = self.view.scope_name(0).split(" ")[0].split(".")[-1]
        syntax = langs.get(syntax, syntax)

        dev_key = setting("pastebin_dev_key", self.view)
        private = setting("pastebin_private", self.view)
        expire = setting("pastebin_expire", self.view)
        url = "https://pastebin.com/api/api_post.php"
        if selection:
            contents = self.view.substr(self.view.sel()[0])
        else:
            contents = self.view.substr(sublime.Region(0, self.view.size()))

        response = requests.post(
            url,
            data={
                "api_dev_key": dev_key,
                "api_paste_code": contents,
                "api_paste_private": private,
                "api_paste_name": paste_name,
                "api_paste_expire_date": expire,
                "api_paste_format": syntax,
                "api_option": "paste",
            },
        )
        if not response.ok:
            print("Pastebin: failed, API response: ", response.text)
            sublime.status_message("Failed, API response: " + response.text)
            return

        sublime.set_clipboard(response.text)
        sublime.status_message("URL copied")
