import os
import requests


import sublime
import sublime_plugin

from .utils import pastbin_langs, setting
from .privatebin_api import private_bin_upload


class PrivatebinShareCommand(sublime_plugin.TextCommand):
    """Create a pastebin and copy the URL in the clipboard.

    > https://privatebin.info
    > https://pastebin.com/doc_api

    TODO: allow choosing other services like
    > https://paste.rs/
    """

    def run(self, edit, selection=False):
        def _run_async():
            paste_name = self.view.file_name()
            if paste_name is not None:
                paste_name = os.path.basename(paste_name)
            else:
                paste_name = "Untitled"

            if selection:
                contents = self.view.substr(self.view.sel()[0])
            else:
                contents = self.view.substr(sublime.Region(0, self.view.size()))

            share_bin_mode = setting("share_bin_mode", self.view)
            if share_bin_mode == "pastebin":
                syntax = pastbin_langs.get(
                    self.view.scope_name(0).split(" ")[0].split(".")[-1]
                )
                dev_key = setting("pastebin_dev_key", self.view)
                private = setting("pastebin_private", self.view)
                expire = setting("pastebin_expire", self.view)
                url = "https://pastebin.com/api/api_post.php"

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
                return

            # Use private bin
            privatebin_instance = setting("privatebin_instance", self.view)
            privatebin_expire = setting("privatebin_expire", self.view)
            url = private_bin_upload(contents, privatebin_instance, privatebin_expire)
            if url:
                sublime.set_clipboard(url)
                sublime.status_message("URL copied")

        sublime.set_timeout_async(_run_async)
