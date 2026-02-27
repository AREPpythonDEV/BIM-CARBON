# -*- coding: utf-8 -*-
import webbrowser

hyperlink = "https://bimcarbone.notion.site/"

try:
    webbrowser.open(hyperlink, new=2)
except Exception as e:
    print("Error opening link: {}".format(str(e)))
