import os


def system(cmd):
    print cmd
    os.system(cmd)

def main():
    system('pyrcc4 icons.qrc -o gui/qt/icons_rc.py')

    system('pyuic4 gui/qt/designer/overviewpage.ui -o gui/qt/overviewpage_ui.py')
    system('pyuic4 gui/qt/designer/chatpage.ui     -o gui/qt/chatpage_ui.py')


if __name__ == '__main__':
    main()
