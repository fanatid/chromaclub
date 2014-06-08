# -*- coding: utf-8 -*-
import os, sys
import shutil

from cx_Freeze import setup, Executable


shutil.rmtree("dist", ignore_errors=True)

#-------------------------------------------------------------------------------
# List build_exe options
#-------------------------------------------------------------------------------
#build_exe              directory for built executables and dependent files, defaults to build/
#optimize               optimization level, one of 0 (disabled), 1 or 2
#excludes               comma separated list of names of modules to exclude
#includes               comma separated list of names of modules to include
#packages               comma separated list of packages to include, which includes all submodules in the package
#namespace_packages     comma separated list of packages to be treated as namespace packages (path is extended using pkgutil)
#replace_paths          Modify filenames attached to code objects, which appear in tracebacks. Pass a comma separated list of paths in the form <search>=<replace>. The value * in the search portion will match the directory containing the entire package, leaving just the relative path to the module.
#path                   comma separated list of paths to search; the default value is sys.path
#init_script            the name of the script to use during initialization which, if given as a relative path, will be joined with the initscripts subdirectory of the cx_Freeze installation; the default value is “Console”
#base                   the name of the base executable to use which, if given as a relative path, will be joined with the bases subdirectory of the cx_Freeze installation; the default value is “Console”
#compressed             create a compressed zip file
#copy_dependent_files   copy all dependent files
#create_shared_zip      create a shared zip file called library.zip which will contain all modules shared by all executables which are built
#append_script_to_exe   append the script module to the executable
#include_in_shared_zip  include the script module in the shared zip file
#icon                   include the icon in the frozen executables on the Windows platform and alongside the frozen executable on other platforms
#constants              comma separated list of constant values to include in the constants module called BUILD_CONSTANTS in form <name>=<value>
#include_files          list containing files to be copied to the target directory; it is expected that this list will contain strings or 2-tuples for the source and destination; the source can be a file or a directory (in which case the tree is copied except for .svn and CVS directories); the target must not be an absolute path
#include_msvcr          include the Microsoft Visual C runtime DLLs and (if necessary) the manifest file required to run the executable without needing the redistributable package installed
#zip_includes           list containing files to be included in the zip file directory; it is expected that this list will contain strings or 2-tuples for the source and destination
#bin_includes           list of names of files to include when determining dependencies of binary files that would normally be excluded; note that version numbers that normally follow the shared object extension are stripped prior to performing the comparison
#bin_excludes           list of names of files to exclude when determining dependencies of binary files that would normally be included; note that version numbers that normally follow the shared object extension are stripped prior to performing the comparison
#bin_path_includes      list of paths from which to include files when determining dependencies of binary files
#bin_path_excludes      list of paths from which to exclude files when determining dependencies of binary files
#silent                 suppress all output except warnings
#-------------------------------------------------------------------------------

build_exe = {
    "build_exe": "dist/",
    "includes": [
        "gui.__init__",
        "gui.club_asset",
        "gui.__init__",
        "gui.qt.application",
        "gui.qt.chatpage",
        "gui.qt.chatpage_ui",
        "gui.qt.icons_rc",
        "gui.qt.mainwindow",
        "gui.qt.overviewpage",
        "gui.qt.overviewpage_ui",
        "gui.qt.wallet",
    ],
    "copy_dependent_files": True,
}


#-------------------------------------------------------------------------------
# List Executable options
#-------------------------------------------------------------------------------
#script                 the name of the file containing the script which is to be frozen
#initScript             the name of the initialization script that will be executed before the actual script is executed; this script is used to set up the environment for the executable; if a name is given without an absolute path the names of files in the initscripts subdirectory of the cx_Freeze package is searched
#base                   the name of the base executable; if a name is given without an absolute path the names of files in the bases subdirectory of the cx_Freeze package is searched
#path                   list of paths to search for modules
#targetDir              the directory in which to place the target executable and any dependent files
#targetName             the name of the target executable; the default value is the name of the script with the extension exchanged with the extension for the base executable
#includes               list of names of modules to include
#excludes               list of names of modules to exclude
#packages               list of names of packages to include, including all of the package’s submodules
#replacePaths           Modify filenames attached to code objects, which appear in tracebacks. Pass a list of 2-tuples containing paths to search for and corresponding replacement values. A search for ‘*’ will match the directory containing the entire package, leaving just the relative path to the module.
#compress               boolean value indicating if the module bytecode should be compressed or not
#copyDependentFiles     boolean value indicating if dependent files should be copied to the target directory or not
#appendScriptToExe      boolean value indicating if the script module should be appended to the executable itself
#appendScriptToLibrary  boolean value indicating if the script module should be appended to the shared library zipfile
#icon                   name of icon which should be included in the executable itself on Windows or placed in the target directory for other platforms
#namespacePackages      list of packages to be treated as namespace packages (path is extended using pkgutil)
#shortcutName           the name to give a shortcut for the executable when included in an MSI package
#shortcutDir            the directory in which to place the shortcut when being installed by an MSI package; see the MSI Shortcut table documentation for more information on what values can be placed here.
#-------------------------------------------------------------------------------
targetName = "wallet"
if sys.platform in ["win32", "cygwin"]:
    targetName += ".exe"

chromaclub_exe = Executable(
    script="chromaclub",
    targetDir="dist",
    targetName=targetName,
    compress=False,
    copyDependentFiles=True,
    appendScriptToExe=True,
    appendScriptToLibrary=False
)


from cx_Freeze.dist import build
build_run_old = build.run
def build_run_new(self):
    retval = build_run_old(self)

    import zipfile
    with zipfile.ZipFile(os.path.join('dist', 'library.zip'), mode='a') as zf:
        fnames = [fname for fname in zf.namelist() if fname.startswith("gui")]
        for fname in fnames:
            zf.writestr('chromaclub_'+fname, zf.read(fname))

    return retval
build.run = build_run_new


setup(
    name="chromaclub",
    version="0.0.1",
    description="",
    classifiers=[
        "Programming Language :: Python",
    ],
    url="",
    keywords="",
    options={
        "build_exe": build_exe,
    },
    executables = [
        chromaclub_exe,
    ],
)
