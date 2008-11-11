# comprehensions/CodeManager.py
"""
TODO: update() is still only in test mode; doesn't actually work yet.
TODO: check() should generate deltas

Extracts, checks and updates code examples in ReST files.

You can just put in the codeMarker and the (indented) first line (containing the
file path) into your ReST file, then run the update program to automatically
insert the rest of the file.
"""
import os, re, sys, shutil, inspect, difflib

restFiles = [os.path.join(d[0], f) for d in os.walk(".") if not "_test" in d[0]
             for f in d[2] if f.endswith(".rst")]

class Languages:
    "Strategy design pattern"

    class Python:
        codeMarker = "::\n\n"
        commentTag = "#"
        listings = re.compile("::\n\n( {4}#.*(?:\n+ {4}.*)*)")

    class Java:
        codeMarker = "..  code-block:: java\n\n"
        commentTag = "//"
        listings = \
            re.compile(".. *code-block:: *java\n\n( {4}//.*(?:\n+ {4}.*)*)")

def shift(listing):
    "Shift the listing left by 4 spaces"
    return [x[4:] if x.startswith("    ") else x for x in listing.splitlines()]

# TEST - makes duplicates of the rst files in a test directory to test update():
dirs = set([os.path.join("_test", os.path.dirname(f)) for f in restFiles])
if [os.makedirs(d) for d in dirs if not os.path.exists(d)]:
    [shutil.copy(f, os.path.join("_test", f)) for f in restFiles]
testFiles = [os.path.join(d[0], f) for d in os.walk("_test")
             for f in d[2] if f.endswith(".rst")]

class Commands:
    """
    Each static method can be called from the command line. Add a new static
    method here to add a new command to the program.
    """

    @staticmethod
    def display(language):
        "Print all the code listings"
        for f in restFiles:
            listings = language.listings.findall(open(f).read())
            if not listings: continue
            print('=' * 60 + "\n" + f + "\n" + '=' * 60)
            for n, l in enumerate(listings):
                print("\n".join(shift(l)))
                if n < len(listings) - 1:
                    print('-' * 60)

    @staticmethod
    def extract(language):
        """Pull the code listings from the ReST files and write each
        listing into its own file"""
        paths = set()
        for f in restFiles:
            for listing in language.listings.findall(open(f).read()):
                listing = shift(listing)
                path = listing[0][len(language.commentTag):].strip()
                if path in paths:
                    print("ERROR: Duplicate file name: %s" % path)
                    sys.exit(1)
                else:
                    paths.add(path)
                path = os.path.join("..", "code", path)
                dirname = os.path.dirname(path)
                if dirname:
                    if not os.path.exists(dirname):
                        os.makedirs(dirname)
                file(path, 'w').write("\n".join(listing))

    @staticmethod
    def check(language):
        "Ensure that external code files exist"
        missing = []
        for path in [code.splitlines()[0] for f in restFiles for code in
                     language.listings.findall(open(f).read())]:
            path = path.strip()[len(language.commentTag):].strip()
            path = os.path.normpath(os.path.join("..", "code", path))
            if not os.path.exists(path):
                missing.append(path)
        if missing:
            print("Missing", language.__name__, "files:")
            for p in missing:
                print(p)
        return missing

    @staticmethod
    def update(language): # Test until it is trustworthy
        "Refresh external code files into ReST files"
        if Commands.check(language):
            print(language.__name__, "update aborted")
            return
        def _update(matchobj):
            listing = shift(matchobj.group(1))
            path = listing[0].strip()[len(language.commentTag):].strip()
            filename = os.path.basename(path).split('.')[0]
            path = os.path.join("..", "code", path)
            code = open(path).read().splitlines()
            for i in difflib.ndiff(listing, code):
                if i.startswith("+ ") or i.startswith("- "):
                    d = difflib.HtmlDiff()
                    if not os.path.exists("_deltas"):
                        os.makedirs("_deltas")
                    open(os.path.join("_deltas", filename + ".html"), 'w')\
                        .write(d.make_file(listing, code))
                    break
            return language.codeMarker + \
                "\n".join([("    " + line).rstrip() for line in listing])
        for f in testFiles:
            updated = language.listings.sub(_update, open(f).read())
            open(f, 'w').write(updated)

if __name__ == "__main__":
    commands = dict(inspect.getmembers(Commands, inspect.isfunction))
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Command line options:")
        for name in commands:
            print(name + ": " + commands[name].__doc__)
    else:
        for language in inspect.getmembers(Languages, inspect.isclass):
            commands[sys.argv[1]](language[1])

       