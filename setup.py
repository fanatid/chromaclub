#!/usr/bin/env python
from setuptools import setup


setup(
    name="chromaclub",
    version="0.1",
    description="",
    long_description="",
    url="",
    keywords="",
    install_requires=[
        "ngcccbase",
    ],
    dependency_links=[
        "https://github.com/bitcoinx/ngcccbase/archive/master.zip#egg=ngcccbase-0.0.4",
    ],
    package_dir={
        "chromaclub_gui": "gui",
    },
    scripts=[
        "chromaclub",
        "chromaclubserver"
    ],
    py_modules=[
        "chromaclub_gui.__init__",
        "chromaclub_gui.club_asset",
        "chromaclub_gui.__init__",
        "chromaclub_gui.qt.application",
        "chromaclub_gui.qt.chatpage",
        "chromaclub_gui.qt.chatpage_ui",
        "chromaclub_gui.qt.icons_rc",
        "chromaclub_gui.qt.mainwindow",
        "chromaclub_gui.qt.overviewpage",
        "chromaclub_gui.qt.overviewpage_ui",
        "chromaclub_gui.qt.wallet",
    ]
)
